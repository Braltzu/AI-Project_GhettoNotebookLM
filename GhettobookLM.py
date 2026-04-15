import os
import streamlit as st
from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI, OpenAIEmbeddings
from langchain.chains import RetrievalQA
# Note: LangChain is modular; you usually import specific components 
# rather than the whole library.
from PyPDF2 import PdfReader
from langchain.text_splitter import CharacterTextSplitter
from langchain.vectorstores import Chroma
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient


# Load variables from a .env file
load_dotenv()

# Asetukset (haetaan esim. ympäristömuuttujista)
AZURE_STORAGE_CONNECTION_STRING = os.environ["AZURE_STORAGE_CONNECTION_STR"]
CONTAINER_NAME = os.environ["CONTAINER_NAME"]


def tallenna_azureen(tiedosto_polku, tiedoston_nimi):
    try:
        # 1. Luodaan yhteys Azureen
        blob_service_client = BlobServiceClient.from_connection_string(AZURE_STORAGE_CONNECTION_STRING)
        
        # 2. Haetaan viite containeriin (kansioon)
        blob_client = blob_service_client.get_blob_client(container=CONTAINER_NAME, blob=tiedoston_nimi)

        # 3. Luetaan paikallinen tiedosto ja lähetetään se
        print(f"Ladataan tiedostoa: {tiedoston_nimi}...")
        with open(tiedosto_polku, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
            
        return f"Tiedosto {tiedoston_nimi} on nyt tallennettu Azureen."
    
    except Exception as e:
        return f"Virhe latauksessa: {e}"

# Testikäyttö
# tallenna_azureen("kokeen_aiheet.pdf", "biologia_koe_1.pdf")