import os
import tempfile
from dotenv import load_dotenv

from fastapi import FastAPI, File, UploadFile, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from azure.storage.blob import BlobServiceClient
from fpdf import FPDF

from typing import TypedDict
from langchain_community.retrievers import AzureAISearchRetriever
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, StateGraph

# ── Env ───────────────────────────────────────────────────────────────────────
load_dotenv()

AZURE_STORAGE_CONNECTION_STRING = os.environ["AZURE_STORAGE_CONNECTION_STR"]
CONTAINER_NAME                  = os.environ["CONTAINER_NAME"]

AZURE_SERVICE    = os.environ["AZURE_SEARCH_SERVICE_NAME"]
AZURE_INDEX      = os.environ["AZURE_SEARCH_INDEX_NAME"]
AZURE_KEY        = os.environ["AZURE_SEARCH_API_KEY"]
CONTENT_FIELD    = os.getenv("AZURE_SEARCH_CONTENT_FIELD", "content")
TOP_K            = int(os.getenv("AZURE_SEARCH_TOP_K", "3"))

AOAI_ENDPOINT    = os.environ["AZURE_OPENAI_ENDPOINT"]
AOAI_KEY         = os.environ["AZURE_OPENAI_API_KEY"]
AOAI_DEPLOYMENT  = os.environ["AZURE_OPENAI_DEPLOYMENT"]
AOAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")

# ── RAG setup ─────────────────────────────────────────────────────────────────
retriever = AzureAISearchRetriever(
    service_name=AZURE_SERVICE,
    index_name=AZURE_INDEX,
    api_key=AZURE_KEY,
    content_key=CONTENT_FIELD,
    top_k=TOP_K,
)

llm = AzureChatOpenAI(
    azure_endpoint=AOAI_ENDPOINT,
    api_key=AOAI_KEY,
    azure_deployment=AOAI_DEPLOYMENT,
    api_version=AOAI_API_VERSION,
)

class State(TypedDict):
    query: str
    context: list[str]
    answer: str

def retrieve_node(state: State) -> dict:
    docs = retriever.invoke(state["query"])
    return {"context": [doc.page_content for doc in docs]}

def generate_node(state: State) -> dict:
    context_block = "\n\n---\n\n".join(state["context"])
    messages = [
        SystemMessage(content=(
            "You are a helpful assistant. "
            "Answer the user's question using ONLY the provided context. "
            "If the context doesn't contain enough information, say so clearly."
        )),
        HumanMessage(content=(
            f"Context:\n\n{context_block}\n\n"
            f"Question: {state['query']}"
        )),
    ]
    response = llm.invoke(messages)
    return {"answer": response.content}

builder = StateGraph(State)
builder.add_node("retrieve", retrieve_node)
builder.add_node("generate", generate_node)
builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)
graph = builder.compile()

# ── Helpers ───────────────────────────────────────────────────────────────────
def upload_to_azure(file_path: str, file_name: str) -> str:
    blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
    blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=file_name)
    with open(file_path, "rb") as data:
        blob_client.upload_blob(data, overwrite=True)
    return f"Uploaded '{file_name}' successfully."

def save_as_pdf(answer_text: str, query_text: str) -> str:
    output_dir = "Processed_Files"
    os.makedirs(output_dir, exist_ok=True)
    clean_name = "".join(x for x in query_text[:20] if x.isalnum()) or "summary"
    file_path = os.path.join(output_dir, f"{clean_name}.pdf")

    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, txt="AI Transformation Result", ln=True, align='C')
    pdf.ln(5)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 10, txt=f"Based on query: {query_text}")
    pdf.ln(5)
    pdf.line(10, pdf.get_y(), 200, pdf.get_y())
    pdf.ln(5)
    pdf.set_font("Arial", size=12)
    safe_text = answer_text.encode('latin-1', 'replace').decode('latin-1')
    pdf.multi_cell(0, 10, txt=safe_text)
    pdf.output(file_path)
    return file_path

# ── App ───────────────────────────────────────────────────────────────────────
app = FastAPI(title="GhettoNotebookLM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # tighten this in production
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/summarize")
async def summarize(
    file: UploadFile = File(...),
    query: str = Form(...),
    summary_length: str = Form("Medium"),
):
    """
    1. Save the uploaded file to a temp location
    2. Upload it to Azure Blob Storage
    3. Run the RAG graph with the user query (+ length hint)
    4. Save result as PDF and return it for download
    """
    # --- 1. Save upload to temp file ---
    suffix = os.path.splitext(file.filename)[-1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        # --- 2. Upload to Azure Blob ---
        upload_to_azure(tmp_path, file.filename)

        # --- 3. Build query with length hint ---
        length_hint = {
            "Short":  "Keep the answer concise, 3–5 sentences.",
            "Medium": "Provide a moderate-length answer, around 150–250 words.",
            "Long":   "Provide a detailed, comprehensive answer.",
        }.get(summary_length, "")

        full_query = f"{query}\n\n[Length instruction: {length_hint}]"

        # --- 4. Run RAG ---
        result = graph.invoke({"query": full_query})
        answer = result["answer"]
        chunks = result["context"]

        # --- 5. Save PDF ---
        pdf_path = save_as_pdf(answer, query)

    finally:
        os.unlink(tmp_path)   # clean up temp file

    # Return both the answer text (for display) and the PDF (for download)
    return JSONResponse({
        "answer": answer,
        "chunks_used": len(chunks),
        "pdf_filename": os.path.basename(pdf_path),
    })


@app.get("/download/{filename}")
def download_pdf(filename: str):
    """Serve a generated PDF by filename."""
    path = os.path.join("Processed_Files", filename)
    if not os.path.exists(path):
        return JSONResponse(status_code=404, content={"error": "File not found"})
    return FileResponse(path, media_type="application/pdf", filename=filename)