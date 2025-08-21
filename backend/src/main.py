from fastapi import FastAPI
from src.api.routes import router
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Line Drive AI", description="Analyze MLB player performance")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/")
def root():
    return {"message": "Line Drive AI!"}
