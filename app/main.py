from fastapi import FastAPI

from app.database import Base, engine
from app.routers import signed_url, upload

Base.metadata.create_all(bind=engine)

app = FastAPI(title="File Service")

app.include_router(upload.router)
app.include_router(signed_url.router)
