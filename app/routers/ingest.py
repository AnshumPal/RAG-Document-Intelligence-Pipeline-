import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.chunker import chunk_text
from app.database import IngestionLog, get_session
from app.embedder import embed_chunks
from app.extractor import extract_text
from app.vector_store import ensure_collection, upsert_chunks

router = APIRouter()

ALLOWED_TYPES = {".pdf", ".docx", ".txt"}


class IngestResponse(BaseModel):
    doc_id: str
    chunk_count: int
    status: str


class DocRecord(BaseModel):
    doc_id: str
    filename: str
    chunk_count: int
    status: str
    ingested_at: datetime


@router.post("/ingest", response_model=IngestResponse)
async def ingest(
    file: UploadFile,
    session: AsyncSession = Depends(get_session),
):
    suffix = "." + file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if suffix not in ALLOWED_TYPES:
        raise HTTPException(status_code=400, detail=f"Unsupported file type '{suffix}'. Allowed: {ALLOWED_TYPES}")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    try:
        text = extract_text(file.filename, content)
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Text extraction failed: {exc}")

    chunks = chunk_text(text)
    if not chunks:
        raise HTTPException(status_code=422, detail="No text content found in document")

    embeddings = await embed_chunks(chunks)

    doc_id = str(uuid.uuid4())
    await ensure_collection()
    await upsert_chunks(doc_id, file.filename, chunks, embeddings)

    log = IngestionLog(
        doc_id=doc_id,
        filename=file.filename,
        chunk_count=len(chunks),
        status="success",
    )
    session.add(log)
    await session.commit()

    return IngestResponse(doc_id=doc_id, chunk_count=len(chunks), status="success")


@router.get("/docs", response_model=list[DocRecord])
async def list_docs(session: AsyncSession = Depends(get_session)):
    result = await session.execute(
        select(IngestionLog).order_by(IngestionLog.ingested_at.desc())
    )
    rows = result.scalars().all()
    return [
        DocRecord(
            doc_id=r.doc_id,
            filename=r.filename,
            chunk_count=r.chunk_count,
            status=r.status,
            ingested_at=r.ingested_at,
        )
        for r in rows
    ]
