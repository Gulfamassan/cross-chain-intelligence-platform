from fastapi import FastAPI

app = FastAPI(
    title="Cross Chain Intelligence Platform",
    version="1.0.0"
)

@app.get("/")
def home():
    return {
        "message": "Cross Chain Intelligence Platform Running Successfully"
    }