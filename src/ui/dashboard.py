import time
from pathlib import Path
import httpx
import pandas as pd
import streamlit as st

# CONFIGURATION
API_URL = "http://api:8000"

st.set_page_config(page_title="BugLens AI Dashboard", layout="wide")

# CUSTOM CSS FOR BETTER VISUALS
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
    return httpx.get(f"{API_URL}{endpoint}")


# REFRESH FRAGMENT
@st.fragment(run_every="30s")
def render_job_table():
    jobs = []
    try:
        response = fetch_api_data("/jobs")
        jobs = response.json()
        if jobs:
            df = pd.DataFrame(jobs)
    except httpx.HTTPError:
        st.error("Connection lost.")
    if jobs:
        df = pd.DataFrame(jobs)
        # Toast notification for background work
        processing = df[df["status"] == "PROCESSING"]
        if not processing.empty:
            st.toast(f"AI is analyzing {len(processing)} video(s)...", icon="⏳")

        # Display simplified table
        cols_to_show = ["id", "status", "created_at", "filename"]
        st.dataframe(df[cols_to_show], width="content", hide_index=True)
        return jobs
    return []


@st.fragment(run_every="30s")
def render_job_details(job_id):
    if not job_id:
        return

    try:
        response = fetch_api_data(f"/status/{job_id}")
        if response.status_code != 200:
            st.warning("Waiting for job record to initialize...")
            return

        detail = response.json()
        if detail is None:
            st.warning("Connecting to job data...")
            return

        status = detail.get("status")

        # VIDEO PLAYER (WITH START TIME)
        raw_path = detail.get("file_path", "")
        if raw_path:
            clean_path = (
                Path("/app") / raw_path
                if not raw_path.startswith("/app")
                else Path(raw_path)
            )
            if clean_path.exists() and clean_path.is_file():
                st.video(str(clean_path), start_time=st.session_state.video_start_time)
            else:
                st.info("Video file syncing...")

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
            result_data = detail.get("result", {})

            # Access the 'bug_events' list
            events = result_data.get("bug_events", [])

            if status == "COMPLETED" and events:
                st.write("Click to jump to visual detection:")

                for event in events:
                    # Get the time for this event
                    t = event.get("time", 0)

                    # Look into the 'visuals' for labels
                    visuals = event.get("visuals", [])
                    if visuals:
                        # Get the first detection from the first frame of this event
                        first_frame_detections = visuals[0].get("detections", [])
                        if first_frame_detections:
                            label = first_frame_detections[0].get("label", "Unknown")
                            conf = first_frame_detections[0].get("conf", 0)

                            # Create the button
                            btn_label = f"{t}s: {label} ({conf:.2f})"
                            if st.button(btn_label, key=f"t_{job_id}_{t}_{label}"):
                                st.session_state.video_start_time = t
                                st.rerun()

            elif status == "PROCESSING":
                st.info("Timeline will generate after processing.")
            else:
                st.write("No specific events detected in this recording.")

    except Exception as e:
        st.error(f"Sync error: {e}")


#  Main UI
st.title("BugLens AI: Video Bug Reports")

# Initial fetch for metrics
try:
    initial_jobs = fetch_api_data("/jobs").json()
except httpx.HTTPError as e:
    initial_jobs = []
    st.error(f"Error fetching jobs: {e}")

m1, m2, m3 = st.columns(3)
m1.metric("Total Reports", len(initial_jobs))
m2.metric("System Status", "Online" if initial_jobs is not None else "Offline")
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
                st.success(f"Job Queued: {res.json()['job_id'][:8]}")
                st.rerun()

    st.divider()
    st.info(
        "**Tip:** Speak clearly during the recording so Whisper can catch the bug context."
    )

# MAIN CONTENT: JOB LIST
st.header("Recent Reports")
jobs_list = render_job_table()

# JOB DETAILS SECTION
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
