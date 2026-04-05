from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.app.api import health, documents, analyses, kb

app = FastAPI(title="K&H2", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(documents.router, prefix="/api")
app.include_router(analyses.router, prefix="/api")
app.include_router(kb.router, prefix="/api")
