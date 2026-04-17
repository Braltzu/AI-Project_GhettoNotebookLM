
#Haku osuuteen tarvittavat kirjastot
import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, BlobClient
from fpdf import FPDF
from pypdf import PdfReader

#Query ja muuhun
from typing import Union, TypedDict
from langchain_community.retrievers import AzureAISearchRetriever
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import AzureChatOpenAI
from langgraph.graph import END, START, StateGraph

# Load variables from a .env file
load_dotenv()

# Asetukset
AZURE_STORAGE_CONNECTION_STRING = os.environ["AZURE_STORAGE_CONNECTION_STR"]
CONTAINER_NAME: str = os.environ["CONTAINER_NAME"]


AZURE_SERVICE    = os.environ["AZURE_SEARCH_SERVICE_NAME"]
AZURE_INDEX      = os.environ["AZURE_SEARCH_INDEX_NAME"]
AZURE_KEY        = os.environ["AZURE_SEARCH_API_KEY"]
CONTENT_FIELD    = os.getenv("AZURE_SEARCH_CONTENT_FIELD", "content")
TOP_K            = int(os.getenv("AZURE_SEARCH_TOP_K", "3"))

AOAI_ENDPOINT    = os.environ["AZURE_OPENAI_ENDPOINT"]
AOAI_KEY         = os.environ["AZURE_OPENAI_API_KEY"]
AOAI_DEPLOYMENT  = os.environ["AZURE_OPENAI_DEPLOYMENT"]
AOAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")


#Määrittää topicin automaattisesti LLM kautta pt1
def identify_topic(file_path: str) -> str:
    reader = PdfReader(file_path)

    text_sample=""
    for page in reader.pages[:2]: #reads first two pages
        text_sample += page.extract_text()

    prompt =f"Analyze the following text and return ONLY a one-word category (e.g. Biology, Finance, Legal, Physics) that describes it:\n\n{text_sample[:2000]}"
    response = llm.invoke(prompt)
    topic = response.content.strip().replace(".", "")
    return topic


#Upload to azure: This is where the files get sent to azure blob storage to be processed/indexed
def upload_to_azure(file_path: str, file_name: str) -> str:
    """Lataa yksittäisen tiedoston Azureen."""
    try:
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=file_name)

        print(f"Ladataan: '{file_name}'...")
        with open(file_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
            
        return f"Tiedosto '{file_name}' ladattu onnistuneesti."
    
    except Exception as e:
        return f"Virhe tiedoston '{file_name}' kohdalla: {e}"


#Mainly just does stuff to the directories that make it possible to handle/process the files
if __name__ == "__main__":
    print("\n--- Aloitetaan kansion skannaus ja lataus ---")

    # 1. Määritetään kansio
    source_dir = "FILES_TO_Process"

    #määritellään topic automaattisesti LLM kautta pt2
    files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
    for filename in files:
        full_path = os.path.join(source_dir, filename)
        auto_topic = identify_topic(full_path)
        upload_to_azure(full_path, filename, auto_topic)



    # Varmistetaan että kansio on olemassa
    if not os.path.exists(source_dir):
        print(f"Virhe: Kansiota '{source_dir}' ei löydy!")
        os.makedirs(source_dir)
        print(f"Kansio '{source_dir}' luotu. Lisää sinne tiedostoja ja aja skripti uudelleen.")
    else:
        # 2. Listataan kaikki tiedostot kansiossa
        files = [f for f in os.listdir(source_dir) if os.path.isfile(os.path.join(source_dir, f))]
        
        if not files:
            print("Kansiosta ei löytynyt ladattavia tiedostoja.")
        else:
            print(f"Löytyi {len(files)} tiedostoa. Aloitetaan siirto...")
            
            # 3. Käydään tiedostot läpi silmukassa
            for filename in files:
                # Muodostetaan täysi polku tiedostoon
                full_path = os.path.join(source_dir, filename)
                
                # Kutsutaan latausfunktiota
                tulos = upload_to_azure(full_path, filename)
                print(tulos)

    print("--- Prosessi valmis ---\n")

    #--------------------LÄHETYS OSUUS OHI---------------------------------------------------------------




    #Tähän vielä data prosessointi mikä tuottaa prosessoidun tiedoston aiheesta x
    def save_as_pdf(answer_text, query_text):
        output_dir = "Processed_Files"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
    
        clean_name = "".join(x for x in query_text[:20] if x.isalnum()) or "summary"
        file_path = os.path.join(output_dir, f"{clean_name}.pdf")

        pdf = FPDF()
        pdf.add_page()

        #title
        pdf.set_font("Arial", 'B', 16)
        pdf.cell(0, 10, txt="AI Transformation Result", ln=True, align='C')
        pdf.ln(5)

        #Sub-header
        pdf.set_font("Arial", 'I', 10)
        pdf.multi_cell(0, 10, txt=f"Based on query: {query_text}")
        pdf.ln(5)
        pdf.line(10, pdf.get_y(), 200, pdf.get_y())
        pdf.ln(5)

        #context
        pdf.set_font("Arial", size=12)
        safe_text = answer_text.encode('latin-1', 'replace').decode('latin-1')
        pdf.multi_cell(0, 10, txt=safe_text)

        pdf.output(file_path)
        return file_path

        


#-------------------QUERY & HAKU OSUUS ALKAA-------------------------------------------------------

# ─── Managed retriever ────────────────────────────────────────────────────────
#
# This is the whole point of "managed" RAG.
# Instead of a local Chroma vector store, we point at an Azure AI Search index.
# Azure handles embedding at query time if semantic/vector search is configured.
#
retriever = AzureAISearchRetriever(
    service_name=AZURE_SERVICE,
    index_name=AZURE_INDEX,
    api_key=AZURE_KEY,
    content_key=CONTENT_FIELD,   # the field in your index that contains the text
    top_k=TOP_K,
)

# ─── LLM (Azure OpenAI via Azure AI Foundry) ─────────────────────────────────
#
# AzureChatOpenAI connects to a model deployment in your Azure AI Foundry hub.
# The deployment name is set in the Portal — it's not the model name itself.
#
llm = AzureChatOpenAI(
    azure_endpoint=AOAI_ENDPOINT,
    api_key=AOAI_KEY,
    azure_deployment=AOAI_DEPLOYMENT,
    api_version=AOAI_API_VERSION,
)

# ─── State ────────────────────────────────────────────────────────────────────

class State(TypedDict):
    query: str           # user question
    context: list[str]   # chunks returned by Azure AI Search
    answer: str          # final LLM response


# ─── Nodes ────────────────────────────────────────────────────────────────────

def retrieve(state: State) -> dict:
    """
    Query Azure AI Search.
    Azure handles the vector search / semantic ranking server-side.
    We receive ready-to-use text chunks — no local embedding required.
    """
    docs = retriever.invoke(state["query"])
    return {"context": [doc.page_content for doc in docs]}


def generate(state: State) -> dict:
    """Generate an answer grounded in the retrieved chunks."""
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


# ─── Graph ────────────────────────────────────────────────────────────────────

builder = StateGraph(State)

builder.add_node("retrieve", retrieve)
builder.add_node("generate", generate)

builder.add_edge(START, "retrieve")
builder.add_edge("retrieve", "generate")
builder.add_edge("generate", END)

graph = builder.compile()


# ─── Run ──────────────────────────────────────────────────────────────────────
#Query loop where you can ask anyting from the given files

if __name__ == "__main__":
    #query = input("To begin asking questions write 'Start'").strip()
    while True:
        query = input("Ask a question about your documents (or type 'exit' to quit): ").strip()
        if query.lower() == 'exit':
            print("Exiting. Goodbye")
            break
        if not query:
            print("Please enter a question.")
            continue

        print(f"\n{'=' * 60}")
        print(f"Query: {query}")
        print("-" * 60)

        result = graph.invoke({"query": query})

        print(f"Retrieved {len(result['context'])} chunk(s) from Azure AI Search:\n")
        for i, chunk in enumerate(result["context"], 1):
            preview = chunk[:200].replace("\n", " ")
            print(f"  [{i}] {preview}...")

        print(f"\nAnswer:\n{result['answer']}")


        #PDF tallennus
        try:
            path = save_as_pdf(result['answer'], query)
            print(f"✅ Success! Your new document is ready at: {path}")
        except Exception as e:
            print(f"❌ Error saving PDF: {e}")


        print("\n" + "=" * 60 + "\n")




