from fastapi import FastAPI
from src.app.api.v1.router import api_router

app = FastAPI(
    title="Sports Calendar API",
    description="Backend calendario deportivo",
    version="1.0.0"
)

@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "¡El servidor está funcionando perfectamente!"}

app.include_router(api_router, prefix="/api/v1")