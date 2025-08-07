from fastapi import FastAPI
from src.api.routes import router

app = FastAPI(title="Line Drive AI", description="Analyze MLB player performance")

app.include_router(router)


@app.get("/")
def root():
    return {"message": "Line Drive AI!"}
