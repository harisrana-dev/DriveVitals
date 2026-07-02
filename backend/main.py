from fastapi import FastAPI
from api.telemetry_routes import router as telemetry_router

app = FastAPI()

app.include_router(telemetry_router, prefix="/api")