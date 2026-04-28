"""
🎨 Image Generation Routes - Advanced Physics-Based Procedural Generation
==========================================================
High-quality, realistic cosmic and scientific visualizations.
Pure math + physics + quantum computing. No external APIs.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, Literal
import logging
import os
import sys
import time

import shared_state as state
from iterative_refiner import IterativeRefiner

logger = logging.getLogger("quantum_ai")
router = APIRouter(prefix="/api")


class ImageRequest(BaseModel):
    prompt: str
    width: Optional[int] = 1024
    height: Optional[int] = 1024
    refine: Optional[bool] = False
    target_score: Optional[float] = 0.7
    max_iterations: Optional[int] = 2
    quantum: Optional[Literal["classic", "hybrid", "full"]] = "hybrid"


@router.post("/image/generate")
async def generate_image(req: ImageRequest):
    """Generate high-quality procedural images from text prompts."""
    start_time = time.time()
    try:
        # Ensure backend dir is in path
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)

        # Import advanced generator
        import image_generator_advanced as ig

        # Choose generation method
        if req.quantum == "classic":
            img = ig.generate_image(req.prompt, req.width, req.height)
            mode = "classical_physics"
            quantum_info = None
        else:
            import quantum_integration as qi
            quantum_mode = "hybrid" if req.quantum == "hybrid" else "full"
            img_array = qi.generate_quantum_image(
                req.prompt, req.width, req.height,
                quantum_mode=quantum_mode
            )
            from PIL import Image
            img = Image.fromarray(img_array)
            mode = f"quantum_{quantum_mode}"
            quantum_info = {
                "mode": quantum_mode,
                "device": "default.qubit",
                "seed_source": "hybrid_classical_quantum"
            }

        # Encode to base64
        from io import BytesIO
        import base64
        buf = BytesIO()
        img.save(buf, format="PNG", quality=95, optimize=True)
        data_url = f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode('utf-8')}"

        elapsed = time.time() - start_time

        response = {
            "image": data_url,
            "prompt": req.prompt,
            "width": req.width,
            "height": req.height,
            "mode": mode,
            "generation_time_seconds": round(elapsed, 2),
            "renderer": "advanced_procedural_physics"
        }

        if quantum_info:
            response["quantum"] = quantum_info

        logger.info(f"Generated: {req.prompt[:50]}... ({req.width}x{req.height}) in {elapsed:.2f}s, mode={mode}")
        return response

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        logger.error(f"Image generation failed: {e}\n{error_trace}")
        raise HTTPException(status_code=500, detail={
            "error": str(e),
            "type": type(e).__name__,
            "traceback": error_trace.split('\n')[-10:]
        })


@router.get("/image/scenes")
async def list_scenes():
    """List all available scene types and their keywords"""
    scenes = {
        "black_hole": "Event horizon, accretion disk, photon ring, gravitational lensing",
        "nebula": "Gas clouds, stellar nurseries, emission nebulae, cosmic dust",
        "galaxy": "Spiral galaxies, galactic arms, star systems, elliptical galaxies",
        "quantum_state": "Wavefunctions, superposition, probability clouds, interference",
        "wormhole": "Einstein-Rosen bridges, spacetime tunnels, portals",
        "supernova": "Stellar explosions, shock waves, expanding shells",
        "planet": "Terrestrial, gas giants, ice worlds, lava planets, atmospheres",
        "fractal": "Mandelbrot, Julia sets, recursive patterns, chaos theory",
        "neural": "Neural networks, brain connectivity, synapses, cognitive maps",
        "consciousness": "Quantum consciousness, Orch-OR, microtubules, awareness fields"
    }
    return {"scenes": scenes, "count": len(scenes)}


@router.get("/image/quantum/presets")
async def list_quantum_presets():
    """List curated quantum presets for specific effects"""
    try:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)
        import quantum_integration as qi

        presets = qi.list_quantum_presets()
        details = {}
        for name in presets:
            p = qi.get_quantum_preset(name)
            details[name] = {
                "description": p.get("description", ""),
                "renderer": p.get("renderer", "nebula"),
                "quantum_mode": p.get("quantum_mode", "hybrid"),
                "example_prompts": p.get("prompts", [])[:3]
            }
        return {"presets": details, "count": len(details)}
    except Exception as e:
        logger.error(f"Failed to list presets: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/image/health")
async def health_check():
    """Health check endpoint for the image generation service"""
    try:
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)

        import image_generator_advanced as ig
        import quantum_integration as qi

        # Quick test
        test_img = ig.generate_image("test", 64, 64)
        test_quantum = qi.generate_quantum_image("test", 64, 64, quantum_mode="classic")

        return {
            "status": "healthy",
            "classical_generator": "operational",
            "quantum_generator": "operational",
            "pennyLane_available": True,
            "test_image_size": test_img.size
        }
    except Exception as e:
        return {
            "status": "degraded",
            "error": str(e),
            "classical_generator": "error",
            "quantum_generator": "error"
        }
