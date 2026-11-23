from contextlib import asynccontextmanager

from fastapi import FastAPI

from database.connection import engine
from database.models import Base
from src.routes import agents, auth, uploads


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="BrandPilot AI",
    description="Multi-agent marketing strategy platform",
    version="1.0.0",
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(agents.router)
app.include_router(uploads.router)


@app.get("/health")
def health():
    return {"status": "ok"}
