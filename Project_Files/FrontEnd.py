import streamlit as st

st.set_page_config(page_title="GhettoNotebookLM PDF-summarizer")
st.title("GhettoNotebookLM PDF-summarizer")

# Upload a file
uploaded_file = st.file_uploader("Choose file", type=["pdf", "txt"])

# Query box for the AI
user_query = st.text_area(
    "Instructions for AI:", 
    placeholder="E.g. 'Summarize this into 5 bullet points' or 'Extract all date-related information.'",
    help="Define exactly what you want the AI to do with the document."
)

# Settings in the expander
with st.expander("Settings"):
    summary_length = st.select_slider(
        "Summary length:",
        options=["Short", "Medium", "Long"],
        #value="Medium"
    )
    focus_area = st.text_input("Specific focus area (optional):", placeholder="e.g. Financials, Legal risks")

# Process the file and query
if uploaded_file:
    if st.button("Generate", type="primary", use_container_width=True):
        with st.spinner("Processing..."):
            st.write("### AI Response")
            st.write("Generating based on your instructions...")
            
            # Esimerkki siitä, mitä lähetettäisiin backendille:
            # final_instruction = f"{user_query}. Focus on {focus_area}. Length: {summary_length}."