# BugLens AI: Intelligent Video Bug Reporting

**BugLens AI** is a distributed video analysis pipeline designed to transform raw screen recordings into actionable developer insights. By fusing Computer Vision (YOLOv8), Speech-to-Text (Whisper), and Large Language Models (Llama 3.2), it automatically detects UI anomalies and generates structured bug reports.



---

## Tech Stack & Implementation Logic

| Technology | Role | Why This Choice? |
| :--- | :--- | :--- |
| **Streamlit** | Frontend Dashboard | Utilizes "Fragments" for independent, live UI updates and `st.cache_data` to ensure efficient API polling. |
| **FastAPI** | Backend API | Provides a high-performance, asynchronous bridge between the UI and the database with native support for large file streams. |
| **Redis / RQ** | Task Queue | Decouples heavy AI processing from the API. This ensures the UI stays responsive while the "Vision Engine" runs in the background. |
| **Ollama (Llama 3.2)** | LLM Reasoning | Orchestrates local intelligence to summarize transcripts and logs into a final report without external data leaks. |
| **YOLOv8** | Vision Engine | Performs frame-by-frame object detection to identify UI elements and potential visual glitches with high confidence. |
| **OpenAI Whisper** | Audio Analysis | Captures the developer's spoken context during the recording, providing the "why" behind the "what." |
| **UV (Astral)** | Environment Mgr | Ensures lightning-fast, reproducible Docker builds and ultra-lean container images. |

---

## Key Features

* **Smart Video Timeline:** Automatically identifies bug events and generates clickable timestamps that jump the video player to exact frames.
* **Contextual Fusion:** Combines visual detection logs with audio transcripts to create a comprehensive "Narrative" of the bug.
* **Live Status Polling:** Fragment-based UI architecture that tracks worker progress (Vision/Audio/Summary) in real-time.
* **Jira-Ready Exports:** One-click "Export to Markdown" feature to move bugs directly into your issue tracker.
* **Dockerized Scalability:** Fully containerized architecture allowing you to scale the number of AI workers based on volume.
---

## Architecture Overview

The system operates as a set of microservices orchestrated via Docker Compose:

1.  **UI Service:** A Streamlit app that handles video uploads and report visualization.
2.  **API Service:** A FastAPI bridge managing the PostgreSQL/SQLite database and file storage.
3.  **Worker Service:** The ML powerhouse that pulls jobs from Redis to run Whisper and YOLO.
4.  **Ollama Service:** A dedicated container for local LLM inference.



---

## Getting Started

### 1. Prerequisites
* Docker and Docker Compose
* (Optional) NVIDIA Container Toolkit for GPU acceleration

### 2. Quick Start
```bash
# Clone the repository
git clone [https://github.com/your-username/buglens.git](https://github.com/your-username/buglens.git)
cd buglens

# Create a data directory for video storage
mkdir data

# Spin up the entire pipeline
docker compose up --build
```


### 3. Usage

* Navigate to http://localhost:8501.
* Upload a .mp4 or .mov bug recording via the sidebar.
* Monitor the "Recent Reports" table; the AI will notify you once analysis is complete.
* Use the Bug Timeline to navigate through detected UI events.

---
                                                Builty by human curiacity