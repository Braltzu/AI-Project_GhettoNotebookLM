import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"   # change if backend runs elsewhere

st.set_page_config(page_title="GhettoNotebookLM PDF-summarizer")
st.markdown(
    "<h1 style='text-align: center; color: red;'>GhettoNotebookLM PDF-summarizer</h1>",
    unsafe_allow_html=True,
)

# ── File uploader ─────────────────────────────────────────────────────────────
uploaded_file = st.file_uploader("Choose file", type=["pdf", "txt"])

if uploaded_file:
    file_type = uploaded_file.type.split("/")[-1].upper()
    st.caption(f"📄 Loaded: `{uploaded_file.name}` ({file_type})")

# ── Query input ───────────────────────────────────────────────────────────────
user_query = st.text_area(
    "Instructions for AI:",
    placeholder="E.g. 'Summarize this into 5 bullet points'",
    max_chars=400,
    help="Maximum length is 400 characters (approx. 100 tokens)."
)
st.caption(f"Characters used: {len(user_query)}/400")

# ── Settings ──────────────────────────────────────────────────────────────────
with st.expander("Settings"):
    summary_length = st.select_slider(
        "Summary length:",
        options=["Short", "Medium", "Long"],
        value="Medium",
    )

# ── Generate button ───────────────────────────────────────────────────────────
generate = st.button(
    "Generate",
    type="primary",
    use_container_width=True,
    disabled=not uploaded_file,
)

# ── Generation logic ──────────────────────────────────────────────────────────
if generate:
    if not user_query.strip():
        st.warning("Please provide instructions before generating.")
    else:
        with st.spinner("Processing..."):
            try:
                response = requests.post(
                    f"{BACKEND_URL}/summarize",
                    files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                    data={"query": user_query, "summary_length": summary_length},
                    timeout=120,
                )
                response.raise_for_status()
                data = response.json()

            except requests.exceptions.ConnectionError:
                st.error("❌ Could not connect to the backend. Is it running on localhost:8000?")
                st.stop()
            except requests.exceptions.HTTPError as e:
                st.error(f"❌ Backend error: {e.response.text}")
                st.stop()

        # ── Show result ───────────────────────────────────────────────────────
        st.success(f"✅ Done! Used {data['chunks_used']} context chunk(s) from Azure Search.")
        st.write("### AI Response")
        st.write(data["answer"])

        # ── Download PDF button ───────────────────────────────────────────────
        pdf_filename = data["pdf_filename"]
        pdf_response = requests.get(f"{BACKEND_URL}/download/{pdf_filename}", timeout=30)

        if pdf_response.status_code == 200:
            st.download_button(
                label="📥 Download as PDF",
                data=pdf_response.content,
                file_name=pdf_filename,
                mime="application/pdf",
            )
        else:
            st.warning("PDF was generated but could not be retrieved for download.")