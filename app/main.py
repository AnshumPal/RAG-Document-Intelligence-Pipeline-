from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database import init_db
from app.routers.ingest import router as ingest_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="RAG Ingestion API", version="1.0.0", lifespan=lifespan)
app.include_router(ingest_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
