from fastapi import FastAPI

from app.api.v1.router import api_router

app = FastAPI(title="Sports Calendar API", description="Personalized sports calendar backend", version="1.0.0")


@app.get("/health", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "The server is up and running"}


app.include_router(api_router, prefix="/api/v1")
