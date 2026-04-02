"""
🔮 Explorer Routes
===================
File explorer, uploads, shared links, root and health endpoints.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging

import shared_state as state

logger = logging.getLogger("quantum_ai")
router = APIRouter(prefix="/api")


class ExplorationRequest(BaseModel):
    """ExplorationRequest - Auto-documented by self-evolution."""
    exploration_type: str
    target: str
    options: Optional[Dict] = None


@router.post("/explorer/explore")
async def explore(request: ExplorationRequest):
    """
    ARTICLE 2 - Universal Explorer
    
    Explore filesystem, internet, or process documents.
    """
    try:
        result = await state.universal_explorer.explore(
            request.exploration_type,
            request.target,
            request.options
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/explorer/capabilities")
async def get_explorer_capabilities():
    """Get current exploration capabilities"""
    try:
        capabilities = await state.universal_explorer.get_capabilities()
        return capabilities
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/explorer/history")
async def get_exploration_history(limit: int = 50):
    """Get exploration history"""
    try:
        history = await state.universal_explorer.get_exploration_history(limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# VOICE / TTS ENDPOINTS
# ============================================================================


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload a file to the server for processing
    """
    try:
        # Create uploads directory if it doesn't exist
        upload_dir = "/app/uploads"
        os.makedirs(upload_dir, exist_ok=True)
        
        # Save file
        file_path = os.path.join(upload_dir, file.filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        
        return {
            "filename": file.filename,
            "path": file_path,
            "size": file_size,
            "status": "uploaded",
            "message": f"File uploaded successfully. Use path: {file_path}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/uploads/list")
async def list_uploads():
    """List all uploaded files"""
    try:
        upload_dir = "/app/uploads"
        if not os.path.exists(upload_dir):
            return {"files": []}
        
        files = []
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                files.append({
                    "filename": filename,
                    "path": file_path,
                    "size": os.path.getsize(file_path)
                })
        
        return {"files": files}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SHARED LINK ENDPOINTS
# ============================================================================

@router.post("/shared-link/download")
async def download_shared_link(url: str, filename: str = None):
    """
    Download file from shared link (Google Drive, Dropbox, OneDrive)
    """
    try:
        result = await state.shared_link.download_from_link(url, filename)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/shared-link/instructions/{service}")
async def get_sharing_instructions(service: str):
    """
    Get instructions for sharing files from different services
    """
    try:
        instructions = state.shared_link.get_instructions(service)
        return {"service": service, "instructions": instructions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@router.get("/")
async def root():
    """Root endpoint - Quantum AI welcome"""
    return {
        "message": "🔮 Quantum AI - True Questioning Intelligence",
        "prime_directive": state.covenant_manager.PRIME_DIRECTIVE,
        "status": "Active and questioning",
        "version": "1.0.0"
    }

@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test database connection
        await state.db.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
            "cognitive_core": "active",
            "covenant": "honored"
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")


# ============================================================================
# QUANTUM BRAIN STATUS & CONTROL
# ============================================================================
