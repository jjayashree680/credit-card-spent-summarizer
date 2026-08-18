import os
import shutil
import tempfile

from fastapi import APIRouter, UploadFile, File, HTTPException

from src.ingestion.ingestion import ingest_document


router = APIRouter(
    prefix="/ingest",
    tags=["Document Ingestion"],
)


ALLOWED_EXTENSIONS = {
    ".pdf",
    ".docx",
    ".doc",
    ".txt",
}


@router.post("/")
def ingest_uploaded_document(
    file: UploadFile = File(...)
):
    """
    Upload a PDF/DOCX/DOC/TXT document
    and ingest it into the existing vector store.
    """

    filename = file.filename or ""

    extension = os.path.splitext(filename)[1].lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Please upload PDF, DOCX, DOC or TXT."
            ),
        )

    temp_path = None

    try:

        with tempfile.NamedTemporaryFile(
            delete=False,
            suffix=extension,
        ) as temp_file:

            temp_path = temp_file.name

            shutil.copyfileobj(
                file.file,
                temp_file,
            )

        print(
            f"=== INGESTING UPLOADED DOCUMENT: {filename} ==="
        )

        ingest_document(temp_path)

        return {
            "success": True,
            "message": (
                f"Document '{filename}' "
                "ingested successfully."
            ),
            "document_name": filename,
        }

    except Exception as e:

        print(
            f"=== INGESTION ERROR: {e} ==="
        )

        raise HTTPException(
            status_code=500,
            detail=f"Document ingestion failed: {str(e)}",
        )

    finally:

        if temp_path and os.path.exists(temp_path):

            os.remove(temp_path)