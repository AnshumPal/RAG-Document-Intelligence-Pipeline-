from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.database import init_db
from app.routers.ingest import router as ingest_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await init_db()
    except Exception as e:
        import logging
        logging.getLogger("uvicorn.error").error(f"DB init failed (is PostgreSQL running?): {e}")
    yield


app = FastAPI(title="RAG Ingestion API", version="1.0.0", lifespan=lifespan)
app.include_router(ingest_router)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    return JSONResponse(status_code=500, content={"detail": str(exc)})


@app.get("/health")
async def health():
    return {"status": "ok"}
