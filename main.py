from fastapi import FastAPI
from routes import image

app = FastAPI()

app.include_router(image.router, prefix="/banana-api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
