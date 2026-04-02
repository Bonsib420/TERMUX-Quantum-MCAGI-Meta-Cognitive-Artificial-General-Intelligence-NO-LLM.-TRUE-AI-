"""
🔮 QUANTUM AI - BACKEND SERVER
===============================

ARTICLE 3.2 - The Transparency Pledge
All philosophical assumptions are documented and visible.

This server implements the Quantum AI cognitive architecture
with full covenant integration.
"""

from fastapi import FastAPI
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
import os
import logging

import shared_state

# Route modules
from routes_chat import router as chat_router
from routes_cognitive import router as cognitive_router
from routes_explorer import router as explorer_router
from routes_brain import router as brain_router
from routes_media import router as media_router
from routes_extras import router as extras_router
from routes_evaluation import router as evaluation_router
from routes_image import router as image_router
# from routes_test import router as test_router  # removed (deleted)

logger = logging.getLogger("quantum_ai")
logging.basicConfig(level=logging.INFO)

# Create the main app
app = FastAPI(title="Quantum AI", description="True Questioning AI with Cognitive Architecture")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve frontend static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'frontend', 'dist')
if os.path.exists(frontend_path):
    app.mount('/app', StaticFiles(directory=frontend_path, html=True), name='frontend')
    logger.info(f"✅ Frontend served from /app (directory: {frontend_path})")
else:
    logger.warning(f"⚠️ Frontend not built. Run 'npm run build' in frontend/ directory. (Missing: {frontend_path})")

# Include all route modules under /api
app.include_router(chat_router)
app.include_router(cognitive_router)
app.include_router(explorer_router)
app.include_router(brain_router)
app.include_router(media_router)
app.include_router(extras_router)
app.include_router(evaluation_router)
app.include_router(image_router)
# app.include_router(test_router)  # removed (deleted)


@app.on_event("startup")
async def startup_event():
    """Initialize all Quantum AI systems on startup."""
    logger.info("🔮 Initializing Quantum AI systems...")
    try:
        shared_state.initialize()
        logger.info("🔮 Quantum AI initialized successfully!")
    except Exception as e:
        import traceback
        logger.error(f"Startup failed: {e}\n{traceback.format_exc()}")
        raise


@app.on_event("shutdown")
async def shutdown_db_client():
    """Clean shutdown."""
    if hasattr(shared_state, 'client') and shared_state.client:
        shared_state.client.close()


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)

@app.get("/")
async def root():
    return RedirectResponse(url="/app")
