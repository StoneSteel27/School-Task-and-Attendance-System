from fastapi import FastAPI, status
from app.core.config import settings
from app.api.v1.api import api_router_v1
from app.core.logging_config import setup_logging

setup_logging()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json"
)

app.include_router(api_router_v1, prefix=settings.API_V1_STR)

@app.get("/")
async def read_root():
    return {"message": f"Hello, welcome to {settings.PROJECT_NAME}!"}

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    return {"status": "healthy"}