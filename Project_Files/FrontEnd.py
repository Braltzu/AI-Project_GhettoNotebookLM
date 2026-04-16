import streamlit as st

st.set_page_config(page_title="GhettoNotebookLM PDF-summarizer")
st.markdown("<h1 style='text-align: center;'>GhettoNotebookLM PDF-summarizer</h1>", unsafe_allow_html = True)

# File uploader (PDF and TXT)
uploaded_file = st.file_uploader("Choose file", type=["pdf", "txt"])


if uploaded_file:
    file_type = uploaded_file.type.split("/")[-1].upper()
    st.caption(f"📄 Loaded: `{uploaded_file.name}` ({file_type})")


# Text area for intructions with maximum length of 400 characters
user_query = st.text_area(
    "Instructions for AI:",
    placeholder="E.g. 'Summarize this into 5 bullet points'",
    max_chars=400,
    help="Maximum length is 400 characters (approx. 100 tokens)."
)

# A counter that shows how many characters the user has typed out of the limit (400)
st.caption(f"Characters used: {len(user_query)}/400")

# Settings expansion where the user can select the summary length from three categories: short, medium, and long
with st.expander("Settings"):
    summary_length = st.select_slider(
        "Summary length:",
        options=["Short", "Medium", "Long"],
        value="Medium"
    )

# Generate button which is disabled until a file is uploaded
generate = st.button(
    "Generate",
    type="primary",
    use_container_width=True,
    disabled=not uploaded_file
)


# Generation logic that gives a warning if there is no user query.
if generate:
    if not user_query.strip():
        st.warning("Please provide instructions before generating.")
    else:
        with st.spinner("Processing..."):
            st.write("### AI Response")
            st.info("Input accepted. Sending to LLM...")