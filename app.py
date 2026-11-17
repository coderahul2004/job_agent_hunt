"""Streamlit interface for JobHunt Agent Squad."""
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

from src.config import OUTPUT_DIR, TOP_N
from src.crew import JobHuntCrew
from src.tools.resume_reader import read_resume

st.set_page_config(page_title="JobHunt Agent Squad", page_icon="🎯", layout="wide")
st.title("🎯 JobHunt Agent Squad")
st.caption("Search jobs, match your resume, tailor applications and track opportunities.")

role = st.text_input("Target job role", value="python developer")
uploaded = st.file_uploader("Upload your resume", type=["txt", "pdf"])

if st.button("🚀 Launch the squad", type="primary", use_container_width=True):
    if not role.strip():
        st.warning("Enter a target job role.")
        st.stop()

    if uploaded is None:
        st.warning("Please upload your resume first.")
        st.stop()

    suffix = Path(uploaded.name).suffix.lower()
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
            temp_file.write(uploaded.getvalue())
            temp_path = Path(temp_file.name)

        try:
            resume_text = read_resume(str(temp_path))
        finally:
            temp_path.unlink(missing_ok=True)

        if not resume_text.strip():
            st.error(
                "No readable text was found in the resume. "
                "If this is a scanned PDF, run OCR first or upload a text-based PDF."
            )
            st.stop()

        with st.spinner("Agents are working. This may take a few minutes..."):
            result = JobHuntCrew().run(role.strip(), resume_text, TOP_N)

        st.success("Crew execution completed.")
        st.subheader("📋 Final Report")
        st.markdown(str(result))

        tailored_path = OUTPUT_DIR / "tailored_applications.md"
        if tailored_path.exists():
            tailored_content = tailored_path.read_text(encoding="utf-8")
            if tailored_content.strip():
                st.subheader("✉️ Tailored Applications")
                st.markdown(tailored_content)
                st.download_button(
                    "Download tailored applications",
                    data=tailored_content,
                    file_name="tailored_applications.md",
                    mime="text/markdown",
                )

        log_path = OUTPUT_DIR / "applications_log.csv"
        if log_path.exists():
            st.subheader("📊 Application Tracker")
            tracker_df = pd.read_csv(log_path)
            st.dataframe(tracker_df, use_container_width=True)
            st.download_button(
                "Download application tracker",
                data=tracker_df.to_csv(index=False).encode("utf-8"),
                file_name="applications_log.csv",
                mime="text/csv",
            )

    except Exception as exc:
        if "RateLimitError" in str(exc) or "rate_limit" in str(exc):
            st.error(
                "Groq rate limit reached (free tier allows 8000 tokens per minute). "
                "Wait 1 minute and click Launch again, or lower TOP_N / JOB_SEARCH_LIMIT in .env."
            )
        else:
            st.error("The job-hunt workflow failed.")
            st.exception(exc)