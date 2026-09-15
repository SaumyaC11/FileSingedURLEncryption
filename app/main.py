from fastapi import FastAPI

from app.database import Base, engine
from app.routers import return_file, signed_url, status, upload

Base.metadata.create_all(bind=engine)

app = FastAPI(title="File Service")

app.include_router(upload.router)
app.include_router(signed_url.router)
app.include_router(status.router)
app.include_router(return_file.router)
