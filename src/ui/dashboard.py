import httpx
import pandas as pd
import streamlit as st

st.set_page_config(page_title="BugLens AI Dashboard", layout="wide")

st.title("🐞 BugLens AI: Video Bug Reports")


try:
    jobs = httpx.get("http://api:8000/jobs").json()
except Exception:
    jobs = []

# Top Level Metrics
col1, col2, col3 = st.columns(3)
col1.metric("Total Reports", len(jobs))
col2.metric("System Status", "Online" if jobs is not None else "Offline")
col3.metric("AI Model", "Llama 3.2 (Ollama)")

st.divider()

# Sidebar for Uploads
with st.sidebar:
    st.header("Upload New Video")
    uploaded_file = st.file_uploader("Choose a bug recording...", type=["mp4", "mov"])
    if st.button("Submit to Pipeline", width="content") and uploaded_file:
        with st.spinner("Uploading to API..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue())}
            response = httpx.post("http://api:8000/upload", files=files)
            st.success(f"Job Queued: {response.json()['job_id']}")
            st.rerun()

# Main Content: Job List
st.header("Recent Reports")
if not jobs:
    st.info("No reports found. Upload a video in the sidebar to get started!")
else:
    # dataframe for a cleaner look
    df = pd.DataFrame(jobs)
    # Reorder columns for better readability
    cols = ["id", "status", "created_at"]
    st.dataframe(df[cols], width="content")

    selected_job = st.selectbox("Select a Job to View Details", [j["id"] for j in jobs])

    if selected_job:
        with st.spinner("Fetching details..."):
            detail = httpx.get(f"http://api:8000/status/{selected_job}").json()

        st.divider()
        col_left, col_right = st.columns([1, 1])

        with col_left:
            st.subheader("🤖 AI Analysis")
            # If the job is still processing, show a progress bar
            if detail.get("status") == "PROCESSING":
                st.warning("Analyzing video with YOLO and Whisper...")
                st.progress(50)
            elif detail.get("status") == "COMPLETED":
                st.markdown(f"### Report Summary\n{detail.get('summary')}")
            else:
                st.error(f"Status: {detail.get('status')}")

        with col_right:
            st.subheader("Metadata & Logs")
            with st.expander("View Raw Fusion Data"):
                st.json(detail.get("result", {}))
