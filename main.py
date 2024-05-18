from fastapi import FastAPI
from .routes import image

app = FastAPI()

app.include_router(image.router, prefix="/banana-api/v1")
