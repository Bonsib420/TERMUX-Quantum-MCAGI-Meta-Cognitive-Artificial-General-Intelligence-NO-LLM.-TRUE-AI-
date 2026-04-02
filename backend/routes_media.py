"""
🔮 Media Routes
================
Voice TTS/transcription and image analysis/generation.
"""

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import uuid
import base64
import logging

import shared_state as state

logger = logging.getLogger("quantum_ai")

# Get OpenAI API key from environment (optional)
api_key = os.environ.get('OPENAI_API_KEY')
router = APIRouter(prefix="/api")


class TTSRequest(BaseModel):
    """TTSRequest - Auto-documented by self-evolution."""
    text: str
    voice: str = "default"


class ImageGenRequest(BaseModel):
    """ImageGenRequest - Auto-documented by self-evolution."""
    prompt: str
    style: str = "default"


@router.post("/voice/tts")
async def text_to_speech(request: TTSRequest):
    """
    Text-to-Speech endpoint
    Returns text formatted for browser's Web Speech API
    """
    try:
        # Clean the text for speech
        text = request.text.strip()
        if not text:
            raise HTTPException(status_code=400, detail="Text is required")
        
        # For now, return the text with speech instructions
        # Can integrate with ElevenLabs or OpenAI TTS later
        return {
            "text": text,
            "voice": request.voice,
            "instructions": "Use browser's speechSynthesis API",
            "ssml": f"<speak>{text}</speak>"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/voice/transcribe")
async def transcribe_audio(audio: UploadFile = File(...)):
    """
    Speech-to-Text endpoint (placeholder)
    Would integrate with Whisper or similar
    """
    try:
        # Save audio temporarily
        audio_path = f"/tmp/audio_{uuid.uuid4().hex}.webm"
        with open(audio_path, "wb") as f:
            content = await audio.read()
            f.write(content)
        
        # For now, return instructions for browser's Web Speech API
        return {
            "status": "received",
            "message": "Audio received. Use browser's SpeechRecognition API for real-time transcription.",
            "file_size": len(content)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# KNOWLEDGE GRAPH ENDPOINTS
# ============================================================================

@router.get("/knowledge/graph")

@router.post("/image/analyze")
async def analyze_image(file: UploadFile = File(...)):
    """Analyze an uploaded image"""
    try:
        import base64
        
        # Read and encode image
        content = await file.read()
        image_base64 = base64.b64encode(content).decode('utf-8')
        
        # Save to uploads
        file_path = f"/app/uploads/{file.filename}"
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Use LLM with image (if supported) or return basic info
        file_size = len(content)
        
        # For now, return image metadata
        # Could integrate with vision models later
        return {
            "status": "success",
            "filename": file.filename,
            "size": file_size,
            "path": file_path,
            "message": "Image uploaded. You can ask me about it in chat!",
            "preview": f"data:image/{file.filename.split('.')[-1]};base64,{image_base64[:100]}..."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class ImageGenRequest(BaseModel):
    prompt: str
    size: Optional[str] = "1024x1024"

@router.post("/image/quantum-svg")
async def generate_image_svg(request: ImageGenRequest):
    """Generate an image from text prompt using quantum semantic processing (no external API)"""
    try:
        import base64
        import random
        import hashlib
        
        # Seed with prompt hash for deterministic but unique per prompt
        seed = int(hashlib.sha256(request.prompt.encode()).hexdigest()[:8], 16)
        rng = random.Random(seed)
        
        # Get semantic concepts from QuantumBrain to influence colors/patterns
        try:
            from quantum_brain import get_quantum_brain
            brain = await get_quantum_brain(state.db)
            semantic_context = brain.collapse_engine.get_semantic_context(request.prompt)
            keywords = semantic_context.get('keywords', [])
            collapse_strength = semantic_context.get('collapse_strength', 0.5)
        except Exception as e:
            logger.error(f"QuantumBrain unavailable for image gen: {e}")
            keywords = []
            collapse_strength = 0.5
        
        # Color palette based on quantum/cyber theme and influenced by prompt
        base_hue = rng.randint(0, 360)
        saturation = 70 + rng.randint(0, 30)
        lightness = 50 + rng.randint(-10, 10)
        
        # Generate SVG with procedural pattern inspired by quantum concepts
        width, height = 1024, 1024
        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
            f'<rect width="100%" height="100%" fill="hsl({base_hue}, 20%, 8%)"/>'
        ]
        
        # Generate quantum "wave" circles based on collapse_strength
        num_circles = int(30 * collapse_strength) + 10
        for i in range(num_circles):
            x = rng.randint(0, width)
            y = rng.randint(0, height)
            radius = rng.randint(20, 200)
            hue = (base_hue + rng.randint(-60, 60)) % 360
            alpha = 0.1 + rng.random() * 0.3
            svg_lines.append(f'<circle cx="{x}" cy="{y}" r="{radius}" fill="hsla({hue}, {saturation}%, {lightness}%, {alpha:.2f})"/>')
        
        # Add "quantum entanglement" lines
        num_lines = 20
        for _ in range(num_lines):
            x1, y1 = rng.randint(0, width), rng.randint(0, height)
            x2, y2 = rng.randint(0, width), rng.randint(0, height)
            hue = (base_hue + 180) % 360  # Complementary
            svg_lines.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="hsla({hue}, {saturation}%, {lightness}%, 0.3)" stroke-width="2"/>')
        
        # Overlay prompt as subtle text
        text_y = height - 50
        for line in [request.prompt[:60] + ('...' if len(request.prompt)>60 else '')]:
            svg_lines.append(f'<text x="50%" y="{text_y}" fill="rgba(255,255,255,0.3)" font-size="24" text-anchor="middle" font-family="monospace">{line}</text>')
            text_y += 30
        
        svg_lines.append('</svg>')
        svg_content = '\n'.join(svg_lines)
        
        image_base64 = base64.b64encode(svg_content.encode('utf-8')).decode('utf-8')
        filename = f"quantum_{uuid.uuid4().hex[:8]}.svg"
        
        # Save to local uploads directory
        uploads_dir = os.path.join(os.path.dirname(__file__), "uploads")
        os.makedirs(uploads_dir, exist_ok=True)
        file_path = os.path.join(uploads_dir, filename)
        with open(file_path, "w") as f:
            f.write(svg_content)
        
        return {
            "status": "success",
            "image_base64": image_base64,
            "filename": filename,
            "path": file_path,
            "prompt": request.prompt,
            "concepts_used": keywords,
            "collapse_strength": collapse_strength,
            "message": "Quantum-generated image (no external API)"
        }
        
    except Exception as e:
        logger.error(f"Image generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# GROWTH NOTIFICATIONS ENDPOINT
# ============================================================================

