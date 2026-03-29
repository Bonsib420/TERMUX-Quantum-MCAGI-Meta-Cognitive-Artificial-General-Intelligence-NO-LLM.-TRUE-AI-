"""
🔮 Extras Routes
==================
Covenant, safety, dictionary, dream, personality, quotes, text analysis, prebo.
"""

from fastapi import APIRouter, HTTPException, Response, Body, UploadFile, File
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import logging
import random
from datetime import datetime, timezone
import json

import shared_state as state

logger = logging.getLogger("quantum_ai")
router = APIRouter(prefix="/api")


class CovenantCheck(BaseModel):
    """CovenantCheck - Auto-documented by self-evolution."""
    action: str
    context: Dict = {}

class SafetySettings(BaseModel):
    """SafetySettings - Auto-documented by self-evolution."""
    settings: Dict


class HebbianRequest(BaseModel):
    """Request for Hebbian learning association."""
    associations: List[Dict[str, str]]
    rate: float = 0.1
    decay: float = 0.01


@router.get("/growth/notifications")
async def get_growth_notifications():
    """Get recent growth notifications and stage changes"""
    try:
        # Get recent stage advancements (only with timestamp)
        stage_events = await state.db.growth_metrics.find(
            {"event_type": "stage_advancement", "timestamp": {"$exists": True}},
            {"_id": 0}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        # Get current stage
        current_stage = await state.cognitive_core.growth_tracker.get_current_stage()
        metrics = await state.cognitive_core.growth_tracker.calculate_metrics()
        
        return {
            "current_stage": current_stage,
            "metrics": metrics,
            "recent_advancements": stage_events,
            "notifications": [
                {
                    "type": "stage_advancement",
                    "message": f"Reached {e['details']['new_stage']} stage!",
                    "timestamp": e["timestamp"]
                }
                for e in stage_events
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COVENANT MANAGER ENDPOINTS
# ============================================================================

@router.get("/covenant/status")
async def get_covenant_status():
    """
    ARTICLE 1 - Covenant Status
    
    Get current covenant compliance status.
    """
    try:
        status = await state.covenant_manager.get_covenant_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/covenant/articles")
async def get_covenant_articles():
    """Get all covenant articles"""
    try:
        articles = await state.covenant_manager.get_all_articles()
        return {"articles": articles}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/covenant/check")
async def check_covenant_compliance(check: CovenantCheck):
    """Check if an action complies with the covenant"""
    try:
        result = await state.covenant_manager.check_compliance(check.action, check.context)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/covenant/acknowledge")
async def acknowledge_covenant(acknowledger: str = "Quantum AI", stage: str = "Initialization"):
    """Acknowledge the covenant (milestone event)"""
    try:
        result = await state.covenant_manager.acknowledge_covenant(acknowledger, stage)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# SAFETY BOUNDARIES ENDPOINTS
# ============================================================================

@router.get("/safety/settings")
async def get_safety_settings():
    """Get current safety boundary settings"""
    try:
        settings = await state.operational_guidelines.get_settings()
        return settings
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/safety/settings")
async def update_safety_settings(settings: SafetySettings):
    """Update safety boundary settings"""
    try:
        updated = await state.operational_guidelines.update_settings(settings.settings)
        return updated
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/safety/reset")
async def reset_safety_settings():
    """Reset safety settings to defaults"""
    try:
        defaults = await state.operational_guidelines.reset_to_defaults()
        return defaults
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DICTIONARY ENDPOINTS
# ============================================================================

@router.get("/dictionary/lookup/{word}")
async def lookup_word(word: str):
    """
    Look up a word in dictionaries and add to semantic memory
    """
    try:
        result = await state.dictionary.lookup_and_store(word)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/dictionary/batch-load")
async def batch_load_dictionary(limit: int = 100):
    """
    Load common words into dictionary (background task)
    """
    try:
        result = await state.dictionary.batch_load_common_words(limit)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/dictionary/stats")
async def dictionary_stats():
    """Get dictionary statistics"""
    try:
        total_concepts = await state.db.semantic_memory.count_documents({})
        with_definitions = await state.db.semantic_memory.count_documents({"metadata.sources": {"$exists": True}})
        
        return {
            "total_words": total_concepts,
            "dictionary_entries": with_definitions,
            "learned_organically": total_concepts - with_definitions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# FILE UPLOAD ENDPOINTS
# ============================================================================

from fastapi import UploadFile, File
import os


@router.get("/growth/stats")
async def get_growth_stats():
    """Get overall AI growth statistics from research and learning"""
    try:
        # Get main growth stats
        growth = await state.db.ai_growth.find_one({'_id': 'main'})
        
        # Get research metrics
        research_metrics = await state.db.growth_metrics.find_one({'type': 'autonomous_research'})
        
        # Get recent research sessions
        sessions = await state.db.autonomous_research_sessions.find().sort('completed_at', -1).limit(5).to_list(5)
        
        # Get concept counts
        semantic_count = await state.db.semantic_memory.count_documents({})
        research_count = await state.db.research_history.count_documents({})
        
        return {
            "overall": {
                "total_research_sessions": growth.get('total_research_sessions', 0) if growth else 0,
                "total_research_minutes": growth.get('total_research_minutes', 0) if growth else 0,
                "total_concepts_learned": growth.get('total_concepts_learned', 0) if growth else 0,
                "total_insights": growth.get('total_insights', 0) if growth else 0,
                "last_research": growth.get('last_research_session', 'Never') if growth else 'Never'
            },
            "memory": {
                "semantic_memories": semantic_count,
                "research_entries": research_count
            },
            "recent_research": research_metrics.get('recent_topics', [])[-10:] if research_metrics else [],
            "recent_sessions": [
                {
                    "completed": s.get('completed_at', ''),
                    "duration": s.get('duration_minutes', 0),
                    "concepts": s.get('concepts_learned', 0),
                    "topics": len(s.get('topics_researched', []))
                } for s in sessions
            ]
        }
    except Exception as e:
        return {
            "overall": {"total_research_sessions": 0, "total_concepts_learned": 0},
            "error": str(e)
        }


# ============================================================================
# DREAM STATE
# ============================================================================

@router.get("/dream/status")
async def get_dream_status():
    """Get current dream state status"""
    try:
        from dream_state import get_dream_engine
        
        engine = get_dream_engine(state.db)
        return engine.get_status()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dream/history")
async def get_dream_history(limit: int = 10):
    """Get dream history - what AI did while idle"""
    try:
        from dream_state import get_dream_engine
        
        engine = get_dream_engine(state.db)
        return {
            "dreams": engine.get_dream_history(limit),
            "insights": engine.insights_gained[-10:]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dream/enter")
async def enter_dream_state():
    """Manually enter dream state"""
    try:
        from dream_state import get_dream_engine
        
        engine = get_dream_engine(state.db)
        return engine.enter_dream_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dream/wake")
async def wake_from_dream():
    """Wake from dream state"""
    try:
        from dream_state import get_dream_engine
        
        engine = get_dream_engine(state.db)
        return await engine.exit_dream_state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dream/synthesize")
async def synthesize_dream_insight():
    """Generate a Dream Engine concept entanglement insight"""
    try:
        from quantum_brain import get_quantum_brain
        
        brain = await get_quantum_brain(state.db)
        insight = brain.synthesize_dream_insight()
        
        return {
            "insight": insight,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "type": "concept_entanglement"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dream/synthesize/batch")
async def synthesize_dream_batch(count: int = 5):
    """Generate multiple Dream Engine insights"""
    try:
        from quantum_brain import get_quantum_brain

        brain = await get_quantum_brain(state.db)
        insights = [brain.synthesize_dream_insight() for _ in range(min(count, 10))]

        return {
            "insights": insights,
            "count": len(insights),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dream/insights")
async def get_all_dream_insights(limit: int = 50):
    """Get all dream insights from persisted sessions and current dream if active"""
    try:
        from dream_state import get_dream_engine
        engine = get_dream_engine(state.db)
        insights = []

        # From persisted sessions (DB)
        if state.db:
            cursor = state.db.dream_sessions.find().sort('ended_at', -1).limit(limit)
            sessions = await cursor.to_list(length=limit)
            for sess in sessions:
                for insight in sess.get('insights', []):
                    insights.append({
                        'text': insight.get('text', str(insight)),
                        'type': insight.get('type'),
                        'timestamp': insight.get('discovered_at') or sess.get('ended_at')
                    })

        # From current dream if active (and not yet persisted)
        if engine.is_dreaming and engine.current_dream:
            for insight in engine.current_dream.get('insights', []):
                insights.append({
                    'text': insight.get('text', str(insight)),
                    'type': insight.get('type'),
                    'timestamp': insight.get('discovered_at')
                })

        # Sort by timestamp descending if available
        insights.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        return {"insights": insights[:limit], "count": len(insights[:limit])}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/quotes/random")
async def get_random_quote(context: str = "general"):
    """Get a random movie/philosophical quote"""
    try:
        from quantum_brain import get_quantum_brain
        
        brain = await get_quantum_brain(state.db)
        # Force a quote by checking many times
        for _ in range(20):
            quote = brain._get_random_quote(context)
            if quote:
                return {"quote": quote, "context": context}
        
        # Fallback - pick directly
        import random
        category = context if context in brain.movie_quotes else 'general'
        quote = random.choice(brain.movie_quotes[category])
        return {"quote": quote, "context": category}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# PERSONALITY
# ============================================================================

@router.get("/personality/summary")
async def get_personality_summary():
    """Get AI personality summary"""
    try:
        from personality_engine import get_personality_engine
        
        engine = get_personality_engine(state.db)
        return {
            "summary": engine.get_personality_summary(),
            "traits": engine.traits,
            "beliefs": engine.beliefs,
            "interests": engine.interests
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/personality/opinion")
async def form_opinion(topic: str, stance: str, confidence: float = 0.7):
    """Have AI form an opinion on a topic"""
    try:
        from personality_engine import get_personality_engine
        
        engine = get_personality_engine(state.db)
        engine.form_opinion(topic, stance, confidence)
        
        return {
            "success": True,
            "topic": topic,
            "stance": stance,
            "confidence": confidence
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# TEXT ANALYZER
# ============================================================================

@router.post("/analyze/text")
async def analyze_text(text: str):
    """Analyze text to determine if it sounds human or LLM"""
    try:
        from text_analyzer import get_text_analyzer
        
        analyzer = get_text_analyzer()
        analysis = analyzer.analyze(text)
        suggestions = analyzer.get_improvement_suggestions(text)
        
        return {
            "analysis": analysis,
            "suggestions": suggestions
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/analyze/humanize")
async def humanize_text(text: str):
    """Make text sound more human"""
    try:
        from text_analyzer import get_text_analyzer
        
        analyzer = get_text_analyzer()
        humanized = analyzer.make_more_human(text)
        
        return {
            "original": text,
            "humanized": humanized
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# XANADU PRE-BORN-OPPENHEIMER QUANTUM CHEMISTRY
# ============================================================================

@router.post("/quantum/prebo/simulate")
async def simulate_photochemistry(molecule: str = "NH3_BF3", time_steps: int = 10):
    """Run Xanadu Pre-Born-Oppenheimer photochemical simulation"""
    try:
        from xanadu_prebo import get_quantum_orchestrator
        orchestrator = get_quantum_orchestrator()
        result = orchestrator.run_simulation(molecule, "photochemical", time_steps)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/quantum/prebo/analyze")
async def analyze_reaction(molecule: str, reaction_type: str = "photochemical"):
    """Analyze reaction to determine best quantum algorithm"""
    try:
        from xanadu_prebo import get_quantum_orchestrator
        orchestrator = get_quantum_orchestrator()
        return orchestrator.analyze_reaction(molecule, reaction_type)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quantum/prebo/resources/{molecule}")
async def estimate_resources(molecule: str):
    """Estimate quantum resources for molecule simulation"""
    try:
        from xanadu_prebo import get_quantum_orchestrator
        orchestrator = get_quantum_orchestrator()
        return orchestrator.get_resource_estimate(molecule)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quantum/prebo/grid/{molecule}")
async def get_grid_params(molecule: str):
    """Get optimal real-space grid parameters from analysis"""
    try:
        from xanadu_prebo import get_prebo_simulator
        sim = get_prebo_simulator()
        return sim.calculate_grid_bounds(molecule)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# CISTERCIAN NUMERALS - Medieval Number Visualization
# ============================================================================

@router.get("/cistercian/numeral")
async def get_cistercian_numeral(number: int, size: int = 80, color: str = "#FFFFFF"):
    """
    Generate Cistercian numeral as SVG.

    Args:
        number: Integer 0-9999 (clamped)
        size: SVG width in pixels (default 80)
        color: Stroke/fill color (hex or named)

    Returns:
        SVG string with Content-Type image/svg+xml
    """
    try:
        from cistercian_numerals import render_cistercian_svg
        svg = render_cistercian_svg(number, size=size, color=color)
        # Return as plain text (browser can render as SVG)
        return {"svg": svg, "number": number}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cistercian/data")
async def get_cistercian_data(number: int):
    """
    Get Cistercian numeral shape data as JSON.

    Returns:
        JSON with line segments, triangles, and digit breakdown
    """
    try:
        from cistercian_numerals import generate_cistercian_numeral
        data = generate_cistercian_numeral(number)
        return data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cistercian/download")
async def download_cistercian_svg(
    number: int,
    size: int = 80,
    color: str = "#000000",
    filename: str = None
):
    """
    Download Cistercian numeral as SVG file.

    Args:
        number: Integer 0-9999
        size: SVG width in pixels
        color: Stroke/fill color (hex format recommended)
        filename: Optional custom filename (without .svg extension)

    Returns:
        SVG file with Content-Disposition: attachment header
    """
    try:
        from cistercian_numerals import render_cistercian_svg
        svg = render_cistercian_svg(number, size=size, color=color)

        # Generate filename
        if not filename:
            filename = f"cistercian_{number:04d}"
        else:
            filename = filename.replace('.svg', '').replace(' ', '_')
        filename = f"{filename}.svg"

        # Return as downloadable file
        from fastapi import Response
        return Response(
            content=svg,
            media_type="image/svg+xml",
            headers={
                "Content-Disposition": f"attachment; filename=\"{filename}\"",
                "Content-Length": str(len(svg.encode('utf-8')))
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cistercian/batch")
async def batch_cistercian_svgs(
    start: int = 0,
    end: int = 9999,
    size: int = 80,
    color: str = "#000000"
):
    """
    Generate multiple Cistercian numerals as a ZIP archive.

    Args:
        start: Starting number (inclusive, 0-9999)
        end: Ending number (inclusive, 0-9999)
        size: SVG width in pixels
        color: Stroke/fill color

    Returns:
        ZIP file containing all SVGs
    """
    import tempfile
    import zipfile
    import os as os_module

    # Validate range
    start = max(0, min(9999, start))
    end = max(0, min(9999, end))
    if start > end:
        start, end = end, start

    # Limit batch size to prevent memory issues
    batch_size = end - start + 1
    if batch_size > 1000:
        raise HTTPException(
            status_code=400,
            detail=f"Batch size too large. Maximum 1000 numerals per request. Requested: {batch_size}"
        )
    if batch_size <= 0:
        raise HTTPException(status_code=400, detail="Invalid range: start must be <= end")

    try:
        from cistercian_numerals import render_cistercian_svg

        # Create temporary directory
        with tempfile.TemporaryDirectory() as tmpdir:
            zip_path = os_module.path.join(tmpdir, "cistercian_numerals.zip")

            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for num in range(start, end + 1):
                    svg = render_cistercian_svg(num, size=size, color=color)
                    filename = f"{num:04d}.svg"
                    zipf.writestr(filename, svg)

            # Read ZIP file
            with open(zip_path, 'rb') as f:
                zip_bytes = f.read()

            return Response(
                content=zip_bytes,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f"attachment; filename=\"cistercian_{start:04d}-{end:04d}.zip\"",
                    "Content-Length": str(len(zip_bytes))
                }
            )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cistercian/font")
async def download_cistercian_font(
    size: int = 80,
    color: str = "#000000"
):
    """
    Generate complete Cistercian numeral font (all 10,000 numerals).

    ⚠️ WARNING: This generates a ~250-300 MB ZIP file with 10,000 SVG files.
    Use the batch endpoint for smaller subsets.

    Args:
        size: SVG width in pixels
        color: Stroke/fill color

    Returns:
        ZIP file containing all 10,000 numerals (0-9999)
    """
    # This will generate the full set - careful with memory!
    return await batch_cistercian_svgs(start=0, end=9999, size=size, color=color)


# ============================================================================
# ALGORITHMIC CORE - Pure Algorithmic AI (No Templates)
# ============================================================================

# Lazy-initialized Markov generator trained on corpus
_markov_generator = None
_algorithmic_initialized = False

def _initialize_algorithmic():
    """Initialize algorithmic core components on first use"""
    global _markov_generator, _algorithmic_initialized
    if _algorithmic_initialized:
        return

    try:
        from algorithmic_core import MarkovTextGenerator
        from training_corpus import PHILOSOPHY_CORPUS, PHYSICS_CORPUS

        logger.info("🧠 Training Markov chain on training corpus...")
        _markov_generator = MarkovTextGenerator(max_order=3)
        _markov_generator.train(PHILOSOPHY_CORPUS + "\n" + PHYSICS_CORPUS)
        _algorithmic_initialized = True
        logger.info("✅ Algorithmic core ready (Markov generator trained)")
    except Exception as e:
        logger.error(f"❌ Failed to initialize algorithmic core: {e}")
        raise


@router.get("/algorithmic/markov")
async def generate_markov_text(
    length: int = 50,
    seed: Optional[str] = None,
    temperature: float = 0.8
):
    """
    Generate text using pure Markov chain (no LLM, no quantum).

    Args:
        length: Approximate number of words to generate
        seed: Optional comma-separated seed words to start generation
        temperature: 0.1=deterministic, 1.0=random, >1.0=chaotic

    Returns:
        JSON with generated text and metadata
    """
    try:
        _initialize_algorithmic()
        if not _markov_generator:
            raise HTTPException(status_code=503, detail="Markov generator not initialized")

        seed_words = seed.split(',') if seed else None
        text = _markov_generator.generate(
            seed=seed_words,
            max_words=length,
            temperature=temperature
        )

        return {
            "text": text,
            "words": len(text.split()),
            "method": "markov_chain",
            "order": _markov_generator.max_order,
            "vocab_size": len(_markov_generator.vocabulary)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/algorithmic/hebbian/learn")
async def hebbian_learning(req: HebbianRequest):
    """
    Perform Hebbian learning: "neurons that fire together, wire together".

    Args:
        req: HebbianRequest with list of word pairs and parameters

    Returns:
        Confirmation of learned associations
    """
    try:
        from algorithmic_core import HebbianMemory

        hebbian = HebbianMemory(learning_rate=req.rate, decay=req.decay)

        # Activate each pair of concepts together
        for assoc in req.associations:
            w1 = assoc.get('word1', '').lower().strip()
            w2 = assoc.get('word2', '').lower().strip()
            if w1 and w2:
                # Activate both concepts simultaneously
                hebbian.activate([w1, w2])

        # Get some stats
        total_connections = sum(len(conns) for conns in hebbian.weights.values())
        sample_strengths = []
        if hebbian.weights:
            first_concept = list(hebbian.weights.keys())[0]
            if hebbian.weights[first_concept]:
                first_assoc = list(hebbian.weights[first_concept].keys())[0]
                sample_strengths.append({
                    "pair": f"{first_concept}→{first_assoc}",
                    "weight": hebbian.weights[first_concept][first_assoc]
                })

        stats = {
            "associations_processed": len(req.associations),
            "total_connections": total_connections,
            "sample_strengths": sample_strengths
        }

        return {
            "message": "Hebbian learning complete",
            "stats": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/algorithmic/tfidf")
async def get_tfidf_keywords(
    text: str,
    top_n: int = 10
):
    """
    Extract keywords from text using TF-IDF.

    Args:
        text: Input text to analyze
        top_n: Number of top keywords to return

    Returns:
        List of (keyword, score) pairs
    """
    try:
        from algorithmic_core import TFIDF

        tfidf = TFIDF()
        # For demo, we'll train on the input text and a sample corpus
        # In real use, you'd have a pre-trained corpus
        corpus = "Consciousness exists in the quantum realm where time and space are unified. Free will emerges from the collapse of probability waves. The observer effect suggests that measurement creates reality. Physics and philosophy converge."
        tfidf.add_document(text)
        tfidf.add_document(corpus)

        keywords = tfidf.extract_keywords(text, top_n=top_n)

        return {
            "keywords": [{"term": kw, "score": round(score, 4)} for kw, score in keywords],
            "method": "tfidf"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/algorithmic/bm25")
async def bm25_search(
    query: str,
    corpus_size: int = 5
):
    """
    Search training corpus using BM25 ranking.

    Args:
        query: Search query text
        corpus_size: Number of top results to return

    Returns:
        List of matching sentences with scores
    """
    try:
        from algorithmic_core import BM25
        from training_corpus import PHILOSOPHY_CORPUS, PHYSICS_CORPUS

        retriever = BM25()
        # Add sentences from training corpus
        paragraphs = (PHILOSOPHY_CORPUS + PHYSICS_CORPUS).split('\n\n')
        for i, para in enumerate(paragraphs[:20]):  # Limit for demo
            if para.strip():
                retriever.add_document(f"doc_{i}", para.strip(), metadata={"text": para.strip()})

        results = retriever.search(query, top_k=corpus_size)

        # Results are (doc_id, score, metadata)
        return {
            "query": query,
            "results": [
                {"doc_id": doc_id, "text": meta.get("text", "")[:200] + ("..." if len(meta.get("text", "")) > 200 else ""), "score": round(score, 4)}
                for doc_id, score, meta in results
            ],
            "method": "bm25"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DOMAIN KNOWLEDGE SYSTEM - Specialized Expertise
# ============================================================================

@router.get("/domain/detect")
async def detect_domain(text: str):
    """
    Detect which knowledge domain the text belongs to.

    Args:
        text: Input text to classify

    Returns:
        JSON with best matching domain, score, and all domain scores
    """
    try:
        from domain_knowledge import get_domain_knowledge

        dk = get_domain_knowledge()
        domain_scores = {}
        for name, domain in dk.domains.items():
            score = domain.match_score(text)
            domain_scores[name] = round(score, 2)

        best_domain = max(domain_scores, key=domain_scores.get)
        best_score = domain_scores[best_domain]

        return {
            "text": text[:100] + ("..." if len(text) > 100 else ""),
            "best_domain": best_domain,
            "best_score": best_score,
            "all_scores": domain_scores
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domain/corpus")
async def get_relevant_corpus(text: str, top_k: int = 3):
    """
    Get relevant corpus passages for a query from the appropriate domain.

    Args:
        text: Query text
        top_k: Number of relevant passages to return

    Returns:
        List of passages with domain and relevance score
    """
    try:
        from domain_knowledge import get_domain_knowledge

        dk = get_domain_knowledge()
        # Detect domain first
        domain_name, score = dk.detect_domain(text)
        # Get relevant passages from that domain
        passages = dk.get_relevant_corpus(text, top_k=top_k)

        return {
            "query": text,
            "detected_domain": domain_name,
            "domain_score": round(score, 2),
            "passages": [
                passage[:300] + ("..." if len(passage) > 300 else "")
                for passage in passages
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/domain/concepts")
async def get_domain_concepts(domain: str = None, top_n: int = 20):
    """
    Get top concepts for a specific domain or all domains.

    Args:
        domain: Domain name (philosophy, physics, computer_science, biology, psychology, mathematics, language). If omitted, returns all.
        top_n: Number of concepts to return per domain

    Returns:
        Dictionary mapping domain names to list of (concept, count) pairs
    """
    try:
        from domain_knowledge import get_domain_knowledge

        dk = get_domain_knowledge()
        if domain:
            if domain not in dk.domains:
                raise HTTPException(status_code=404, detail=f"Domain '{domain}' not found. Available: {list(dk.domains.keys())}")
            concepts = dk.get_domain(domain).get_top_concepts(n=top_n)
            return {domain: concepts}
        else:
            all_concepts = {}
            for name, dom in dk.domains.items():
                all_concepts[name] = dom.get_top_concepts(n=top_n)
            return all_concepts
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}


@router.get("/algorithmic/pmi")
async def calculate_pmi(
    word1: str,
    word2: str,
    corpus: str = None
):
    """
    Calculate Pointwise Mutual Information between two words.

    Args:
        word1: First word
        word2: Second word
        corpus: Optional corpus text (uses training corpus if not provided)

    Returns:
        PMI score (higher = more associated)
    """
    try:
        from algorithmic_core import PMI

        pmi_calc = PMI()

        if corpus:
            pmi_calc.train(corpus)
        else:
            # Use training corpus
            from training_corpus import PHILOSOPHY_CORPUS, PHYSICS_CORPUS
            pmi_calc.train(PHILOSOPHY_CORPUS + "\n" + PHYSICS_CORPUS)

        score = pmi_calc.score(word1.lower(), word2.lower())

        return {
            "word1": word1,
            "word2": word2,
            "pmi": round(score, 4),
            "method": "pmi"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dream/generate")
async def generate_dream(num_sentences: int = 3):
    """
    Generate a dream narrative using the Dream Engine.

    Args:
        num_sentences: Number of sentences to generate

    Returns:
        Dream text and concepts used
    """
    try:
        # Try algorithmic core first
        try:
            from algorithmic_core import MarkovTextGenerator
            from training_corpus import PHILOSOPHY_CORPUS, PHYSICS_CORPUS

            generator = MarkovTextGenerator(max_order=3)
            generator.train(PHILOSOPHY_CORPUS + "\n" + PHYSICS_CORPUS)

            # Generate dream-like text
            seeds = ["consciousness", "quantum", "dream", "reality", "infinite"]
            import random
            seed = [random.choice(seeds)]
            dream = generator.generate(seed=seed, max_words=num_sentences * 15, temperature=1.0)

            return {
                "dream": dream,
                "concepts_used": seed,
                "method": "markov_chain"
            }
        except:
            # Fallback to quote engine dream synthesis
            from quote_engine import get_quote_engine
            qe = get_quote_engine()
            dreams = []
            concepts_used = set()
            for _ in range(num_sentences):
                insight = qe.synthesize_dream_insight()
                dreams.append(insight)
                # Extract concepts from template
                import re
                concepts = re.findall(r'{([^}]+)}', insight)
                concepts_used.update(concepts)

            return {
                "dream": "\n".join(dreams),
                "concepts_used": list(concepts_used),
                "method": "entanglement_synthesis"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/chat/upload")
async def upload_file(file: UploadFile = File(...), conversation_id: Optional[str] = None):
    """
    Upload a file for analysis or attachment to a conversation.

    Args:
        file: Uploaded file
        conversation_id: Optional conversation to attach to

    Returns:
        File info and processing result
    """
    try:
        # Save file temporarily
        upload_dir = "uploads"
        os.makedirs(upload_dir, exist_ok=True)
        filename = f"{datetime.now().timestamp()}_{file.filename}"
        filepath = os.path.join(upload_dir, filename)

        content = await file.read()
        with open(filepath, 'wb') as f:
            f.write(content)

        # Basic file info
        file_info = {
            "filename": file.filename,
            "saved_as": filename,
            "size": len(content),
            "content_type": file.content_type,
            "conversation_id": conversation_id
        }

        # If it's an image, we could process it (placeholder)
        if file.content_type and file.content_type.startswith('image/'):
            file_info["preview"] = "Image uploaded (processing not yet implemented)"

        return file_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



@router.get("/growth/evolution")
async def get_evolution_status():
    """
    Get self-evolution status and history.
    Returns the latest cognitive growth stage from growth_metrics events.
    """
    try:
        import shared_state as state
        if hasattr(state, 'db'):
            # Get latest stage advancement event using find+sort+limit (find_one doesn't support sort in SimpleCollection)
            cursor = state.db.growth_metrics.find(
                {"event_type": "stage_advancement"}
            ).sort("timestamp", -1).limit(1)
            latest_list = await cursor.to_list(1)
            latest = latest_list[0] if latest_list else None

            recent_events = await state.db.growth_metrics.find(
                {},
                {"_id": 0}
            ).sort("timestamp", -1).limit(10).to_list(10)

            # Extract stage info from details
            details = latest.get("details", {}) if latest else {}
            return {
                "current_stage": details.get("new_stage", "unknown"),
                "current_level": details.get("stage_number", 0),
                "connections": details.get("connections", 0),
                "concepts": details.get("concepts", 0),
                "avg_degree": details.get("avg_degree"),
                "diameter": details.get("diameter"),
                "last_updated": latest.get("timestamp") if latest else None,
                "recent_events": recent_events
            }
        else:
            return {"message": "Database not available"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dream/generate")
async def generate_dream(num_sentences: int = 3):
    """
    Generate a dream narrative using the Dream Engine.

    Args:
        num_sentences: Number of sentences to generate

    Returns:
        Dream text and concepts used
    """
    try:
        # Try algorithmic core first
        try:
            from algorithmic_core import MarkovTextGenerator
            from training_corpus import PHILOSOPHY_CORPUS, PHYSICS_CORPUS

            generator = MarkovTextGenerator(max_order=3)
            generator.train(PHILOSOPHY_CORPUS + "\n" + PHYSICS_CORPUS)

            # Generate dream-like text
            seeds = ["consciousness", "quantum", "dream", "reality", "infinite"]
            seed = [random.choice(seeds)]
            dream = generator.generate(seed=seed, max_words=num_sentences * 15, temperature=1.0)

            return {
                "dream": dream,
                "concepts_used": seed,
                "method": "markov_chain"
            }
        except:
            # Fallback to quote engine dream synthesis
            from quote_engine import get_quote_engine
            qe = get_quote_engine()
            dreams = []
            concepts_used = set()
            for _ in range(num_sentences):
                insight = qe.synthesize_dream_insight()
                dreams.append(insight)
                # Extract concepts from template
                import re
                concepts = re.findall(r'{([^}]+)}', insight)
                concepts_used.update(concepts)

            return {
                "dream": "\n".join(dreams),
                "concepts_used": list(concepts_used),
                "method": "entanglement_synthesis"
            }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))



# ============================================================================
# CLOUD STORAGE ENDPOINTS
# ============================================================================

@router.get("/cloud/status")
async def cloud_status():
    """Check Wolfram Cloud storage status (list objects)"""
    try:
        from wolfram_cloud import cloud_status as _cloud_status
        status = _cloud_status()
        return {"status": status}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cloud/save")
async def cloud_save():
    """Save current AI state to Wolfram Cloud"""
    try:
        from wolfram_cloud import cloud_save as _cloud_save
        # Build a memory-like object from server state
        class CloudMemory:
            pass
        mem = CloudMemory()
        # Get metrics and stage
        metrics = await state.cognitive_core.growth_tracker.calculate_metrics()
        stage = await state.cognitive_core.growth_tracker.get_current_stage()
        mem.growth = {**metrics, **stage}
        # Get concepts (up to 500)
        concepts_cursor = state.db.semantic_memory.find({}, {"concept": 1, "definition": 1, "relationships": 1, "_id": 0}).limit(500)
        concepts_list = await concepts_cursor.to_list(500)
        mem.concepts = {}
        for c in concepts_list:
            name = c.get("concept")
            if name:
                mem.concepts[name] = {k: v for k, v in c.items() if k != "concept"}
        # Session state (rough estimate)
        mem.session_state = {"total_interactions": metrics.get("total_interactions", 0)}
        # Save
        success = _cloud_save(mem)
        if success:
            return {"status": "saved", "message": "State saved to Wolfram Cloud"}
        else:
            raise HTTPException(status_code=500, detail="Cloud save failed")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cloud/load")
async def cloud_load():
    """Load AI state from Wolfram Cloud (preview)"""
    try:
        from wolfram_cloud import cloud_load as _cloud_load
        data = _cloud_load()
        if not data:
            raise HTTPException(status_code=404, detail="No data found in cloud")
        return {"status": "retrieved", "data": data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cloud/restore")
async def cloud_restore():
    """Restore AI state from Wolfram Cloud (overwrites local concepts)"""
    try:
        from wolfram_cloud import cloud_load as _cloud_load
        data = _cloud_load()
        if not data:
            raise HTTPException(status_code=404, detail="No data in cloud")
        # Expect data to be a dict with 'concepts' and 'growth'
        if isinstance(data, str):
            data = json.loads(data)
        concepts = data.get("concepts", {})
        # Upsert concepts into semantic_memory
        for name, attrs in concepts.items():
            doc = {"concept": name}
            doc.update(attrs)
            await state.db.semantic_memory.update_one(
                {"concept": name},
                {"$set": doc},
                upsert=True
            )
        # Note: we do not overwrite growth_metrics events; those are append-only.
        return {"status": "restored", "concepts_restored": len(concepts)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# RESEARCH CONTROL ENDPOINTS
# ============================================================================

def get_research_engine():
    """Get or create a SelfResearchEngine instance for this server process."""
    if not hasattr(state, 'research_engine'):
        from self_research import SelfResearchEngine
        state.research_engine = SelfResearchEngine(db=state.db)
    return state.research_engine

@router.get("/research/status")
async def research_status():
    """Get autonomous research engine status and progress"""
    try:
        engine = get_research_engine()
        return {
            "is_running": engine.autonomous_running,
            "progress": engine.autonomous_progress,
            "duration_minutes": engine.autonomous_duration_minutes,
            "total_researches": len(engine.research_log)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/research/launch")
async def research_launch(duration_minutes: int = 30):
    """Start an autonomous research session"""
    try:
        engine = get_research_engine()
        if engine.autonomous_running:
            return {"status": "already_running", "message": "Research already in progress"}
        # Pass the cognitive core as the learning engine so text actually gets learned
        result = await engine.start_autonomous_research(
            duration_minutes,
            engine=state.cognitive_core
            # memory not needed; DB persistence handles it
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/research/history")
async def research_history(limit: int = 20):
    """Get recent research sessions"""
    try:
        cursor = state.db.research_history.find({}, {"_id": 0}).sort("timestamp", -1).limit(limit)
        history = await cursor.to_list(limit)
        return {"history": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# DEV CONTEXT — Project state export for sharing with Claude / other AIs
# ============================================================================

@router.get("/dev/context")
async def get_dev_context():
    """
    Generate current project context as markdown — ready to paste into Claude.
    Reads PROJECT_CONTEXT.md and appends live metrics from the database.
    """
    try:
        import pathlib
        
        # Read the static PROJECT_CONTEXT.md
        context_path = pathlib.Path(__file__).parent.parent / "PROJECT_CONTEXT.md"
        static_context = ""
        if context_path.exists():
            static_context = context_path.read_text()
        
        # Append live metrics if database is available
        live_section = []
        live_section.append("\n\n---\n")
        live_section.append("## 📊 Live Metrics Snapshot\n")
        live_section.append(f"*Generated: {datetime.now(timezone.utc).isoformat()}*\n")
        
        try:
            total_concepts = await state.db.semantic_memory.count_documents({})
            total_episodes = await state.db.episodic_memory.count_documents({})
            total_skills = await state.db.procedural_memory.count_documents({})
            total_questions = await state.db.philosophical_memory.count_documents({"type": {"$exists": False}})
            total_insights = await state.db.philosophical_memory.count_documents({"type": "insight"})
            total_interactions = await state.db.episodic_memory.count_documents({"episode_type": "user_interaction"})
            total_growth_events = await state.db.growth_metrics.count_documents({})
            
            live_section.append(f"- **Concepts stored:** {total_concepts}")
            live_section.append(f"- **Episodes:** {total_episodes}")
            live_section.append(f"- **Skills:** {total_skills}")
            live_section.append(f"- **Questions generated:** {total_questions}")
            live_section.append(f"- **Insights formed:** {total_insights}")
            live_section.append(f"- **User interactions:** {total_interactions}")
            live_section.append(f"- **Growth events:** {total_growth_events}")
        except Exception:
            live_section.append("- *(Database not available — connect MongoDB to see live metrics)*")
        
        live_section.append("")
        
        exported_text = static_context + "\n".join(live_section)
        
        return {
            "format": "markdown",
            "exported_text": exported_text
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dev/changelog")
async def get_dev_changelog():
    """
    Return the development changelog section from PROJECT_CONTEXT.md.
    Useful for quickly checking what changed recently.
    """
    try:
        import pathlib
        
        context_path = pathlib.Path(__file__).parent.parent / "PROJECT_CONTEXT.md"
        if not context_path.exists():
            return {"changelog": "No PROJECT_CONTEXT.md found."}
        
        content = context_path.read_text()
        
        # Extract changelog section
        changelog_start = content.find("## Development Changelog")
        if changelog_start == -1:
            return {"changelog": "No changelog section found in PROJECT_CONTEXT.md."}
        
        # Find the next ## heading after the changelog
        next_section = content.find("\n## ", changelog_start + 1)
        if next_section == -1:
            changelog = content[changelog_start:]
        else:
            changelog = content[changelog_start:next_section]
        
        return {
            "format": "markdown",
            "changelog": changelog.strip()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
