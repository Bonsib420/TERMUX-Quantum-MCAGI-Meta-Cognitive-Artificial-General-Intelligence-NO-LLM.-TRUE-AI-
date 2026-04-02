"""
🔮 Brain & Research Routes
============================
Brain status, quantum gates, wolfram, research, and evolution endpoints.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging
from datetime import datetime, timezone

import shared_state as state

logger = logging.getLogger("quantum_ai")
router = APIRouter(prefix="/api")


class AutonomousResearchRequest(BaseModel):
    """AutonomousResearchRequest - Auto-documented by self-evolution."""
    topic: str


@router.get("/brain/status")
async def get_brain_status():
    """Get Quantum Brain status - the TRUE AI status"""
    try:
        from quantum_brain import get_quantum_brain
        
        brain = await get_quantum_brain(state.db)
        
        # Get vocabulary stats from the generator
        vocab = brain.generator.vocabulary if hasattr(brain.generator, 'vocabulary') else {}
        vocab_count = sum(len(v) if isinstance(v, (list, dict)) else 0 for v in vocab.values()) if vocab else 0
        
        # Get memory stats
        semantic_count = await state.db.semantic_memory.count_documents({})
        episodic_count = await state.db.episodic_memory.count_documents({})
        philosophical_count = await state.db.philosophical_memory.count_documents({})
        
        return {
            "status": "active",
            "brain_type": "QuantumBrain",
            "llm_enabled": brain.llm_enabled,
            "llm_role": "disabled_pure_quantum",
            "vocabulary": {
                "total_words": vocab_count,
                "generator_type": type(brain.generator).__name__
            },
            "memory": {
                "semantic": semantic_count,
                "episodic": episodic_count,
                "philosophical": philosophical_count
            },
            "quantum_components": {
                "pennylane": brain.pennylane is not None,
                "wolfram": brain.wolfram is not None,
                "dream_engine": brain.dream_engine is not None,
                "evolution_engine": brain.evolution_engine is not None
            },
            "philosophy": {
                "prime_directive": "No Refusal - Help user any way possible",
                "word_philosophy": "All words are neutral tools",
                "meaning_source": "Intent and context, not words themselves"
            }
        }
    except Exception as e:
        return {
            "status": "initializing",
            "error": str(e)
        }


@router.post("/brain/toggle-llm")
async def toggle_brain_llm(enabled: bool = True):
    """Toggle whether LLM polishing is enabled"""
    try:
        from quantum_brain import get_quantum_brain
        
        brain = await get_quantum_brain(state.db)
        brain.llm_enabled = enabled
        
        mode = "polisher" if enabled else "raw"
        return {
            "success": True,
            "llm_enabled": enabled,
            "mode": f"Quantum Brain with {'LLM grammar polishing' if enabled else 'raw output (no LLM)'}",
            "message": f"LLM {'enabled as grammar polisher' if enabled else 'disabled - using pure Quantum Brain output'}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brain/learn-word")
async def teach_brain_word(word: str, definition: str, part_of_speech: str = "unknown"):
    """Teach the Quantum Brain a new word"""
    try:
        from quantum_brain import get_quantum_brain
        
        brain = await get_quantum_brain(state.db)
        brain.vocabulary.add_word(word, definition, part_of_speech)
        
        return {
            "success": True,
            "word": word,
            "definition": definition,
            "message": f"Quantum Brain learned new word: {word}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/brain/learn-concept")
async def teach_brain_concept(concept: str, meaning: str):
    """Teach the Quantum Brain a new concept"""
    try:
        from quantum_brain import get_quantum_brain
        
        brain = await get_quantum_brain(state.db)
        brain.vocabulary.add_concept(concept, meaning)
        
        return {
            "success": True,
            "concept": concept,
            "meaning": meaning,
            "message": f"Quantum Brain learned new concept: {concept}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# QUANTUM GATE CONTROL
# ============================================================================

@router.post("/quantum/gate")
async def apply_quantum_gate(gate: str):
    """Apply a quantum gate (hadamard, pauli_x, pauli_z, measure)"""
    try:
        from quantum_brain import get_quantum_brain
        
        brain = await get_quantum_brain(state.db)
        result = brain.apply_gate(gate)
        
        return {
            "success": True,
            "gate_applied": gate,
            "quantum_state": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quantum/state")
async def get_quantum_state():
    """Get current quantum state"""
    try:
        from quantum_brain import get_quantum_brain
        
        brain = await get_quantum_brain(state.db)
        
        return {
            "quantum_state": brain.quantum_state.to_dict(),
            "pennylane_available": brain.pennylane is not None
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# WOLFRAM ALPHA
# ============================================================================

@router.post("/wolfram/query")
async def wolfram_query(query: str):
    """Query Wolfram Alpha for mathematical/scientific answers"""
    try:
        from wolfram_integration import get_wolfram_engine
        
        wolfram = get_wolfram_engine()
        result = wolfram.query(query)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SELF-RESEARCH
# ============================================================================

@router.post("/research/query")
async def research_query(query: str, reason: str = "user_request"):
    """Perform autonomous research on a topic"""
    try:
        # Direct DDGS test
        from ddgs import DDGS
        ddgs = DDGS()
        direct_results = list(ddgs.text(query, max_results=3))
        logger.info(f"[RESEARCH DEBUG] Direct DDGS returned {len(direct_results)} results for '{query}'")
        
        from self_research import get_research_engine
        engine = await get_research_engine(state.db)
        result = await engine.research(query, reason)
        
        # If engine returned 0 but direct worked, use direct results
        if len(result.get('results', [])) == 0 and len(direct_results) > 0:
            logger.info(f"[RESEARCH DEBUG] Using direct results")
            result['results'] = [{'title': r.get('title',''), 'body': r.get('body',''), 'href': r.get('href','')} for r in direct_results]
            # Re-extract concepts
            all_text = ' '.join([r.get('body', '') for r in direct_results])
            words = [w.lower() for w in all_text.split() if len(w) > 4]
            result['new_concepts'] = list(set(words))[:10]
        
        return result
    except Exception as e:
        logger.error(f"[RESEARCH ERROR] {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research/stats")
async def get_research_stats():
    """Get research statistics"""
    try:
        from self_research import get_research_engine
        
        engine = await get_research_engine(state.db)
        return engine.get_research_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# AUTONOMOUS RESEARCH (30-60 MINUTES)
# ============================================================================

class AutonomousResearchRequest(BaseModel):
    duration_minutes: int = 30

@router.post("/research/autonomous/start")
async def start_autonomous_research(request: AutonomousResearchRequest):
    """Start autonomous research session (30-60 minutes)"""
    try:
        from self_research import get_research_engine
        
        engine = await get_research_engine(state.db)
        # Verify db is passed and write a test entry
        logger.info(f"[RESEARCH] Starting autonomous research, db={state.db is not None}")
        
        # Direct test write
        try:
            await state.db.research_test.insert_one({
                'test': 'autonomous_start',
                'timestamp': datetime.now(timezone.utc).isoformat()
            })
            logger.info("[RESEARCH] Test write to DB successful")
        except Exception as write_err:
            logger.error(f"[RESEARCH] Test write failed: {write_err}")
        
        result = await engine.start_autonomous_research(request.duration_minutes)
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/research/autonomous/stop")
async def stop_autonomous_research():
    """Stop autonomous research session"""
    try:
        from self_research import get_research_engine
        
        engine = await get_research_engine(state.db)
        result = engine.stop_autonomous_research()
        
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/research/autonomous/progress")
async def get_autonomous_research_progress():
    """Get autonomous research progress"""
    try:
        from self_research import get_research_engine
        
        engine = await get_research_engine(state.db)
        return engine.get_autonomous_progress()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SELF-EVOLUTION
# ============================================================================

@router.get("/evolution/status")
async def get_evolution_status():
    """Get self-evolution status"""
    try:
        from self_evolution_core import get_evolution_engine
        
        engine = get_evolution_engine(state.db)
        return engine.get_evolution_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/evolution/trigger")
async def trigger_evolution():
    """Manually trigger self-evolution (user-initiated)"""
    try:
        from self_evolution_core import get_evolution_engine
        
        engine = get_evolution_engine(state.db)
        result = await engine.auto_evolve()
        
        return {
            "success": True,
            "evolution_result": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evolution/analyze/{filename}")
async def analyze_code_file(filename: str):
    """Analyze a code file for potential improvements"""
    try:
        from self_evolution_core import get_evolution_engine
        
        engine = get_evolution_engine(state.db)
        analysis = engine.read_own_code(filename)
        improvements = engine.identify_improvements(filename)
        
        # Strip raw code from response to keep it lightweight
        if 'code' in analysis:
            del analysis['code']
        
        return {
            "analysis": analysis,
            "improvements": improvements,
            "improvement_count": len(improvements)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/evolution/analyze-all")
async def analyze_all_code():
    """Analyze all modifiable code files"""
    try:
        from self_evolution_core import get_evolution_engine
        
        engine = get_evolution_engine(state.db)
        all_analyses = engine.analyze_all_code()
        
        # Collect all improvements
        all_improvements = []
        for filename in engine.modifiable_files:
            improvements = engine.identify_improvements(filename)
            for imp in improvements:
                imp['file'] = filename
                all_improvements.append(imp)
        
        # Sort by priority
        all_improvements.sort(key=lambda x: x.get('priority', 99))
        
        # Strip raw code from response
        for key, analysis in all_analyses.get('analyses', {}).items():
            if 'code' in analysis:
                del analysis['code']
        
        return {
            "summary": {
                "files_analyzed": all_analyses['files_analyzed'],
                "total_lines": all_analyses['total_lines'],
                "total_classes": all_analyses['total_classes'],
                "total_functions": all_analyses['total_functions'],
                "total_improvements": len(all_improvements)
            },
            "improvements": all_improvements,
            "files": {k: v for k, v in all_analyses.get('analyses', {}).items() if 'error' not in v}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


