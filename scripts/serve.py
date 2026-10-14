"""Local demo. Mock payments until .env has sandbox keys."""

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("repairbrake.app:app", host="127.0.0.1", port=8766, reload=False)
