import os
import pickle
import faiss
from PyPDF2 import PdfReader
from openai import OpenAI
from dotenv import load_dotenv
import numpy as np

# Carrega as variáveis do .env
load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

VECTORDIR = "vectordb"
PDFDIR = "pdfs"

INDEX_FILE = os.path.join(VECTORDIR, "index.faiss")
META_FILE = os.path.join(VECTORDIR, "meta.pkl")

def dividir_texto(texto, tamanho=1000, sobreposicao=200):
    chunks = []
    inicio = 0
    while inicio < len(texto):
        fim = inicio + tamanho
        chunk = texto[inicio:fim]
        chunks.append(chunk)
        inicio += tamanho - sobreposicao
    return chunks

def processar_pdfs():
    textos = []
    metadados = []

    for nome_arquivo in os.listdir(PDFDIR):
        if nome_arquivo.endswith(".pdf"):
            caminho = os.path.join(PDFDIR, nome_arquivo)
            print(f"[INFO] Processando {nome_arquivo}")
            leitor = PdfReader(caminho)
            texto_pdf = ""
            for pagina in leitor.pages:
                texto_pdf += pagina.extract_text() or ""
            chunks = dividir_texto(texto_pdf)

            for i, chunk in enumerate(chunks):
                textos.append(chunk)
                metadados.append({
                    "arquivo": nome_arquivo,
                    "conteudo": chunk,
                    "id": f"{nome_arquivo} - trecho {i+1}"
                })

    print(f"[INFO] Gerando embeddings para {len(textos)} pedaços...")

    embeddings = []
    for chunk in textos:
        response = client.embeddings.create(
            model="text-embedding-3-small",
            input=chunk
        )
        vetor = response.data[0].embedding
        embeddings.append(vetor)

    matriz = np.array(embeddings).astype("float32")
    index = faiss.IndexFlatL2(len(embeddings[0]))
    index.add(matriz)

    os.makedirs(VECTORDIR, exist_ok=True)
    faiss.write_index(index, INDEX_FILE)
    with open(META_FILE, "wb") as f:
        pickle.dump(metadados, f)

    print("[✅ SUCESSO] Base vetorial criada com sucesso.")

def buscar_trechos(pergunta, k=3):
    if not os.path.exists(INDEX_FILE) or not os.path.exists(META_FILE):
        print("[❌ ERRO] Base vetorial não encontrada. Rode processar_pdfs() antes.")
        return []

    index = faiss.read_index(INDEX_FILE)
    with open(META_FILE, "rb") as f:
        metadados = pickle.load(f)

    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=pergunta
    )
    vetor_pergunta = np.array(response.data[0].embedding).astype("float32").reshape(1, -1)

    distancias, indices = index.search(vetor_pergunta, k)

    trechos = []
    for i in indices[0]:
        if 0 <= i < len(metadados):
            trecho = metadados[i]
            trecho_id = trecho.get("id", f"Trecho {i}")
            print(f"[📄 TRECHO ENCONTRADO] {trecho_id}")
            trechos.append(trecho["conteudo"])
        else:
            print(f"[⚠️ AVISO] Índice {i} fora dos metadados.")

    return trechos
