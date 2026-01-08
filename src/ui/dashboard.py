import time
from pathlib import Path

import httpx
import pandas as pd
import streamlit as st

# CONFIGURATION
API_URL = "http://api:8000"

st.set_page_config(page_title="BugLens AI Dashboard", layout="wide")

# Initialize session state for navigation
if "video_start_time" not in st.session_state:
    st.session_state.video_start_time = 0

# Custom CSS
st.markdown(
    """
    <style>
    [data-testid="stMetric"] {
        background-color: rgba(28, 131, 225, 0.1);
        padding: 15px;
        border-radius: 10px;
        border: 1px solid rgba(28, 131, 225, 0.2);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# Cache for only 2 seconds to keep it "live" but deduplicated
@st.cache_data(ttl=2)
def fetch_api_data(endpoint):
    try:
        response = httpx.get(f"{API_URL}{endpoint}")
        if response.status_code == 200:
            return response
        else:
            st.error(f"API Error {response.status_code}: {endpoint}")
            return None
    except Exception as e:
        st.error(f"Connection Error: {e}")
        return None


# REFRESH FRAGMENT
@st.fragment(run_every="30s")
def render_job_table():
    response = fetch_api_data("/jobs")
    if response and response.status_code == 200:
        jobs = response.json()
        if jobs:
            df = pd.DataFrame(jobs)
            processing = df[df["status"] == "PROCESSING"]
            if not processing.empty:
                st.toast(f"AI is analyzing {len(processing)} video(s)...", icon="⏳")

            cols_to_show = ["id", "status", "created_at", "filename"]
            st.dataframe(df[cols_to_show], width="content", hide_index=True)
            return jobs
    return []


@st.fragment(run_every="30s")  # Speed up refresh for active investigation
def render_job_details(job_id):
    if not job_id:
        return

    response = fetch_api_data(f"/status/{job_id}")
    if not response or response.status_code != 200:
        st.warning("Connecting to job data...")
        return

    detail = response.json()
    status = detail.get("status")

    # VIDEO PLAYER SECTION
    st.subheader("Video Evidence")

    # Toggle for AI Vision
    show_vision = st.toggle(
        "Enable AI Vision Overlay",
        help="Show detection bounding boxes",
        key=f"vision_toggle_{job_id}",
    )

    # --- 1. Resolve Path Logic ---
    raw_path = detail.get("file_path")
    vision_path = detail.get("vision_file_path")

    # Determine which file to actually show
    video_to_play = vision_path if (show_vision and vision_path) else raw_path

    if video_to_play:
        if not str(video_to_play).startswith("/app"):
            full_path = Path("/app") / video_to_play
        else:
            full_path = Path(video_to_play)

        if full_path.exists():
            st.video(
                str(full_path),
                start_time=st.session_state.video_start_time,
                format="video/mp4",
            )
        else:
            st.warning(f"Looking for file: {full_path}")
            if raw_path:
                st.video(str(Path("/app") / raw_path), format="video/mp4")
    else:
        st.info("No video path provided by the API.")

    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("AI Analysis")
        if status == "COMPLETED":
            st.markdown(detail.get("summary", "Summary missing."))
            report_md = f"# BUG REPORT: {job_id}\n\n{detail.get('summary')}"
            st.download_button(
                "Export to Markdown", report_md, file_name=f"bug_{job_id[:8]}.md"
            )
        elif status == "PROCESSING":
            st.warning("Vision engine running... (Auto-updating)")
            st.progress(65)
        else:
            st.info(f"Status: {status}")

    with col_r:
        st.subheader("Bug Timeline")

        result_data = detail.get("result")

        if status == "COMPLETED" and isinstance(result_data, dict):
            events = result_data.get("bug_events", [])

            if events:
                st.write("Click to jump to visual detection:")
                for event in events:
                    t = event.get("time", 0)
                    visuals = event.get("visuals", [])
                    if visuals:
                        first_det = visuals[0].get("detections", [])
                        if first_det:
                            label = first_det[0].get("label", "Unknown")
                            conf = first_det[0].get("conf", 0)
                            if st.button(
                                f"{t}s: {label} ({conf:.2f})",
                                key=f"t_{job_id}_{t}_{label}",
                            ):
                                st.session_state.video_start_time = t
                                st.rerun()
            else:
                st.write("No specific events detected.")

        elif status == "PROCESSING":
            st.info("Timeline is being generated...")
            st.spinner("Analyzing frames...")
        else:
            st.write("No timeline data available yet.")


#  Main UI
st.title("BugLens AI Dashboard")

# Metrics
res_metrics = fetch_api_data("/jobs")
initial_jobs = res_metrics.json() if res_metrics else []
m1, m2, m3 = st.columns(3)
m1.metric("Total Reports", len(initial_jobs))
m2.metric("System Status", "Online" if res_metrics else "Offline")
m3.metric("AI Engine", "Llama 3.2 (Ollama)")

st.divider()

# SIDEBAR: UPLOAD
with st.sidebar:
    st.header("Upload New Video")
    uploaded_file = st.file_uploader("Drop bug recording here...", type=["mp4", "mov"])
    if st.button("Submit to Pipeline", width="content") and uploaded_file:
        with st.spinner("Uploading..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            res = httpx.post(f"{API_URL}/upload", files=files)
            if res.status_code == 200:
                st.cache_data.clear()
                st.success(f"Job Queued: {res.json()['job_id'][:8]}")
                time.sleep(0.5)
                st.rerun()

    st.divider()
    st.info(
        "**Tip:** Speak clearly during the recording so Whisper can catch the bug context."
    )

# job table
st.header("Recent Reports")
jobs_list = render_job_table()

if jobs_list:
    st.divider()
    selected_id = st.selectbox(
        "Select a Job to Investigate", [j["id"] for j in jobs_list]
    )

    if selected_id:
        # Action Bar
        detail = fetch_api_data(f"/status/{selected_id}").json()

        # Action Bar: Delete & Export
        if st.button("Delete Job", type="primary"):
            with st.spinner("Deleting..."):
                try:
                    response = httpx.delete(f"{API_URL}/jobs/{selected_id}")
                    if response.status_code == 200:
                        st.success("Job deleted successfully!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(f"API Error {response.status_code}: {response.text}")
                except Exception as e:
                    st.error(f"Connection Error: {e}")
        render_job_details(selected_id)
else:
    st.info("No reports found yet. Use the sidebar to upload your first video.")
