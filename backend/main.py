from fastapi import FastAPI

app = FastAPI(title="The Lenny Growth Assistant")


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "service": "lenny-growth-assistant"
    }