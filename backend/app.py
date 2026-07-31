from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print(f"Starting {settings.APP_NAME}")
    if settings.DEBUG_FORCE_SCENARIO:
        print(
            "!" * 70
            + f"\nDEBUG SCENARIO FORCING ACTIVE: {settings.DEBUG_FORCE_SCENARIO}"
            " — remove before demo\n"
            + "!" * 70
        )
    yield
    print("Shutting down...")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.get("/ping")
async def ping():
    return {"message": "pong"}