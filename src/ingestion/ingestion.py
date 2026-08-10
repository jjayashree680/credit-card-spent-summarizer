import os
from dotenv import load_dotenv
from langchain_community.document_loaders import (
    TextLoader,
    UnstructuredWordDocumentLoader,
    PyPDFLoader,
)
from langchain_text_splitters import (
    RecursiveCharacterTextSplitter,
)
from src.core.db import get_vector_store
from sqlalchemy import create_engine, text


load_dotenv()

PG_CONNECTION = os.getenv(
    "PG_CONNECTION_STRING"
)

def load_document(file_path):
    """
    Load PDF, TXT, DOCX or DOC files.
    """
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".pdf":
        loader = PyPDFLoader(file_path)
    elif ext == ".txt":
        loader = TextLoader(
            file_path,
            encoding="utf-8",
        )
    elif ext == ".docx" or ext == ".doc":
        loader = UnstructuredWordDocumentLoader(
            file_path
        )
    else:
        raise ValueError(
            f"Unsupported file extension: {ext}"
        )
    return loader.load(), ext


# ============================================================
# 2. CREATE VECTOR INDEX
# ============================================================

def index_add():
    """
    Configure pgvector and create the cosine
    similarity index.
    """
    engine = create_engine(
        PG_CONNECTION
    )
    with engine.connect() as conn:
        # Enable pgvector extension
        conn.execute(
            text(
                """
                CREATE EXTENSION IF NOT EXISTS vector
                """
            )
        )
        # Embedding dimension:
        # text-embedding-3-small = 1536
        conn.execute(
            text(
                """
                ALTER TABLE langchain_pg_embedding
                ALTER COLUMN embedding
                TYPE vector(1536)
                """
            )
        )
        # Create cosine similarity index
        conn.execute(
            text(
                """
                CREATE INDEX IF NOT EXISTS
                langchain_pg_embedding_vector_idx
                ON langchain_pg_embedding
                USING ivfflat
                (embedding vector_cosine_ops)
                WITH (lists = 100)
                """
            )
        )
        conn.commit()


# ============================================================
# 3. INGEST DOCUMENT
# ============================================================

def ingest_document(file_path):
    """
    Load, split and store the Credit Card
    Knowledge Base into PostgreSQL/pgvector.
    """

    # --------------------------------------------------------
    # Load document
    # --------------------------------------------------------

    docs, ext = load_document(
        file_path
    )

    print(
        "Documents loaded: "
        + str(len(docs))
    )

    # --------------------------------------------------------
    # Add metadata
    # --------------------------------------------------------

    for doc in docs:

        doc.metadata.update(
            {
                "source": file_path,

                "document_name": os.path.basename(
                    file_path
                ),

                "document_extension": ext,

                "page": doc.metadata.get(
                    "page",
                    None,
                ),

                "category": "credit_card_support",

                "last_updated": os.path.getmtime(
                    file_path
                ),
            }
        )

    # --------------------------------------------------------
    # Split document into chunks
    # --------------------------------------------------------

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100,
    )

    chunks = splitter.split_documents(
        docs
    )

    print(
        "Chunks: "
        + str(len(chunks))
    )

    # --------------------------------------------------------
    # Get PGVector store
    # --------------------------------------------------------

    vector_store = get_vector_store(
        "CreditCardSummarizerVectorStore"
    )

    # --------------------------------------------------------
    # Add documents
    # --------------------------------------------------------

    vector_store.add_documents(
        chunks
    )

    # --------------------------------------------------------
    # Create index
    # --------------------------------------------------------

    index_add()

    print(
        "==== Credit Card Knowledge Base "
        "Ingestion completed ===="
    )


# ============================================================
# 4. MAIN
# ============================================================

if __name__ == "__main__":

    ingest_document(
        "data/KB_Credit_Card_Spend_Summarizer.docx"
    )