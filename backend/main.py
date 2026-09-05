from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import BACKEND_HOST, BACKEND_PORT, FRONTEND_URL
from backend.api.investigation import router as investigation_router
from backend.api.incidents import router as incidents_router
from backend.api.explain import router as explain_router
from backend.api.transactions import router as transactions_router

app = FastAPI(
    title="Settlement Intelligence API",
    description="Recon Flow — deterministic fintech settlement investigation platform",
    version="0.4.0",
)

# CORS configuration — allow local React dev server and common variants
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

# Mount routers
app.include_router(investigation_router)
app.include_router(incidents_router)
app.include_router(explain_router)
app.include_router(transactions_router)



@app.get("/")
def root():
    return {
        "status": "healthy",
        "service": "Settlement Intelligence API",
        "version": "0.4.0",
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "Settlement Intelligence API",
        "version": "0.4.0",
        "endpoints": {
            "docs": "/docs",
            "openapi": "/openapi.json",
            "investigate_post": "POST /api/investigate",
            "investigate_get": "GET /api/investigate/{transaction_id}",
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host=BACKEND_HOST, port=BACKEND_PORT, reload=True)

