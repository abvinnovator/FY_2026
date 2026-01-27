import logging
import os
import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

# Ensure local package imports resolve when launched from repo root or other cwd
CURRENT_DIR = os.path.dirname(__file__)
if CURRENT_DIR not in sys.path:
	sys.path.insert(0, CURRENT_DIR)

from src.core.config import get_settings

# Import API routes (implemented incrementally)
try:
	from src.channels.banking_api_routes import router as banking_router
except Exception as import_exc:  # Avoid hard failure during initial scaffold
	banking_router = None
	logging.getLogger(__name__).warning(
		"Banking API routes not yet available: %s", import_exc
	)


@asynccontextmanager
async def lifespan(app: FastAPI):
	"""Application startup/shutdown hooks.

	- Load configuration
	- Later: initialize DB connections, vector stores, etc.
	"""
	settings = get_settings()
	logging.basicConfig(level=logging.INFO)
	logging.getLogger(__name__).info("Starting Banking Ops API in %s mode", "debug" if settings.allow_debug else "prod")
	yield
	logging.getLogger(__name__).info("Shutting down Banking Ops API")


app = FastAPI(
	title="Intelligent Banking Operations Agent",
	version="0.1.0",
	lifespan=lifespan,
)

# Allow local dev frontends to call the API
app.add_middleware(
	CORSMiddleware,
	allow_origins=[
		"http://127.0.0.1:5173",
		"http://localhost:5173",
		"http://127.0.0.1:5174",
		"http://localhost:5174",
		"http://127.0.0.1:5175",
		"http://localhost:5175",
		"http://127.0.0.1:5176",
		"http://localhost:5176",
	],
	allow_credentials=True,
	allow_methods=["*"],
	allow_headers=["*"]
)


@app.get("/health")
async def root():
	return {"status": "ok", "service": "banking-ops"}


if banking_router is not None:
	app.include_router(banking_router, prefix="/api/v1")

# Serve built frontend if available
frontend_dist = os.path.join(os.path.dirname(__file__), "frontend", "dist")
if os.path.isdir(frontend_dist):
	try:
		app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
	except Exception:
		pass


def run():
	"""Convenience entry to run with `python main.py`.
	Prefer `uvicorn main:app --reload` in development.
	"""
	import uvicorn
	settings = get_settings()
	uvicorn.run(
		"main:app",
		host=os.getenv("API_HOST", "0.0.0.0"),
		port=int(os.getenv("API_PORT", "8000")),
		reload=settings.allow_debug,
	)


if __name__ == "__main__":
	run()


