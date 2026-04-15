import os
from dotenv import load_dotenv
from azure.storage.blob import BlobServiceClient, BlobClient
from typing import Union

# Load variables from a .env file
load_dotenv()

# Asetukset
AZURE_STORAGE_CONNECTION_STRING = os.environ["AZURE_STORAGE_CONNECTION_STR"]
CONTAINER_NAME: str = os.environ["CONTAINER_NAME"]

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

if __name__ == "__main__":
    print("\n--- Aloitetaan kansion skannaus ja lataus ---")

    # 1. Määritetään kansio
    source_dir = "FILES_TO_Process"
    
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