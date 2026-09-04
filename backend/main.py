from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import BACKEND_HOST, BACKEND_PORT, FRONTEND_URL

app = FastAPI(
    title="Settlement Intelligence API",
    description="AI-powered fintech settlement investigation and systemic incident detection platform",
    version="0.1.0",
)

# CORS configuration
origins = [
    FRONTEND_URL,
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "Settlement Intelligence API",
        "version": "0.1.0",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Settlement Intelligence API",
        "version": "0.1.0",
        "endpoints": {
            "docs": "/docs",
            "openapi": "/openapi.json",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)
