"""
📊 Evaluation Routes
====================
Rubric-based scoring for Quantum MCAGI.
"""

from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, List, Optional, Any
import logging

import shared_state as state
from evaluation_engine import get_evaluation_engine

logger = logging.getLogger("quantum_ai")
router = APIRouter(prefix="/api")


class EvaluateRequest(BaseModel):
    """Request payload for evaluation."""
    input_text: str
    response: str
    context: Optional[Dict[str, Any]] = None  # can include internal_questions, semantic_context, etc.


class EvaluateResponse(BaseModel):
    """Response with rubric scores."""
    scores: Dict[str, int]  # dimension -> score 0-4
    summary: Optional[str] = None


@router.post("/evaluate", response_model=EvaluateResponse)
async def evaluate_response(req: EvaluateRequest):
    """
    Evaluate a response using the RQR³ rubric.
    
    Requires the QuantumBrain to be initialized (provides collapse_engine and markov).
    """
    try:
        # Grab the quantum brain to access collapse engine and markov
        if hasattr(state, 'quantum_brain') and state.quantum_brain is not None:
            brain = state.quantum_brain
        else:
            from quantum_brain import get_quantum_brain
            brain = await get_quantum_brain(state.db)
            state.quantum_brain = brain
        
        collapse_engine = brain.collapse_engine if brain else None
        markov = None
        # Get hybrid generator's markov if accessible
        try:
            from hybrid_generator import HybridGenerator
            # Not stored directly; we'll pass None for now; evaluation can still run
        except:
            pass
        
        # Create evaluation engine
        engine = get_evaluation_engine(
            collapse_engine=collapse_engine,
            markov=markov,
            config={}
        )
        
        # Compute scores
        raw_scores = engine.score_response(
            input_text=req.input_text,
            response=req.response,
            context=req.context or {}
        )
        # Remove any None values (e.g., question_generation_quality when not applicable)
        scores = {k: v for k, v in raw_scores.items() if v is not None}
        
        # Generate a brief summary text
        dimensions = ['coherence', 'fluency', 'uniqueness', 'grounding',
                     'personality_authenticity', 'implementation_fidelity',
                     'emergent_behavior', 'question_generation_quality']
        summary_parts = []
        for dim in dimensions:
            if dim in scores:
                summary_parts.append(f"{dim.capitalize()}: {scores[dim]}/4")
        summary = " | ".join(summary_parts)
        
        return EvaluateResponse(scores=scores, summary=summary)
        
    except Exception as e:
        logger.error(f"Evaluation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
