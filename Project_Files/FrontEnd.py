import streamlit as st

st.set_page_config(page_title="GhettoNotebookLM PDF-summarizer")
st.title("GhettoNotebookLM PDF-summarizer")

uploaded_file = st.file_uploader("Choose file", type=["pdf", "txt"])

# Query box with maximum character limit 
user_query = st.text_area(
    "Instructions for AI:", 
    placeholder="E.g. 'Summarize this into 5 bullet points'",
    max_chars=400,
    help="Maximum length is 400 characters (approx. 100 tokens)."
)

# Showing character count to keep track of the input length
st.caption(f"Characters used: {len(user_query)}/400")

with st.expander("Settings"):
    summary_length = st.select_slider(
        "Summary length:",
        options=["Short", "Medium", "Long"],
        value="Medium"
    )

if uploaded_file:
    # Checking that instructions are not empty before generation
    if st.button("Generate", type="primary", use_container_width=True):
        if not user_query:
            st.warning("Please provide instructions first!")
        else:
            with st.spinner("Processing..."):
                st.write("### AI Response")
                st.info("Input accepted. Sending to LLM...")