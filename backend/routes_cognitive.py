"""
🔮 Cognitive Routes
====================
Quantum status, memories, growth, knowledge graph, memory export/import.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone

import shared_state as state

router = APIRouter(prefix="/api")


class MemoryImport(BaseModel):
    """MemoryImport - Auto-documented by self-evolution."""
    semantic: List[Dict] = []
    episodic: List[Dict] = []
    procedural: List[Dict] = []


@router.get("/quantum/status")
async def quantum_status():
    """Get comprehensive cognitive status"""
    try:
        status = await state.cognitive_core.get_status()
        return status
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quantum/memories/semantic")
async def get_semantic_memories(limit: int = 50):
    """Retrieve semantic memory (concepts)"""
    try:
        concepts = await state.cognitive_core.semantic_memory.get_all_concepts(limit)
        return {"concepts": concepts}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quantum/memories/episodic")
async def get_episodic_memories(limit: int = 50):
    """Retrieve episodic memory (experiences)"""
    try:
        episodes = await state.cognitive_core.episodic_memory.recall_recent_episodes(limit)
        return {"episodes": episodes}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quantum/memories/procedural")
async def get_procedural_memories(limit: int = 50):
    """Retrieve procedural memory (skills)"""
    try:
        skills = await state.cognitive_core.procedural_memory.get_all_skills(limit)
        return {"skills": skills}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quantum/memories/philosophical")
async def get_philosophical_memories(answered: bool = False, limit: int = 50):
    """Retrieve philosophical memory (questions and insights)"""
    try:
        if answered:
            questions = await state.cognitive_core.philosophical_memory.get_unanswered_questions(limit)
        else:
            questions = await state.cognitive_core.philosophical_memory.get_unanswered_questions(limit)
        
        insights = await state.cognitive_core.philosophical_memory.get_insights(limit)
        
        return {
            "questions": questions,
            "insights": insights
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/quantum/growth")
async def get_growth_metrics():
    """Get growth metrics, current stage, and recent events"""
    try:
        metrics = await state.cognitive_core.growth_tracker.calculate_metrics()
        stage = await state.cognitive_core.growth_tracker.get_current_stage()
        
        # Fetch recent growth events (stage advancements) with timestamp
        recent_events = []
        try:
            events_cursor = state.db.growth_metrics.find(
                {"event_type": "stage_advancement", "timestamp": {"$exists": True}},
                {"_id": 0}
            ).sort("timestamp", -1).limit(5)
            recent_events = await events_cursor.to_list(5)
        except Exception:
            pass  # If collection doesn't exist yet, ignore
        
        return {
            "metrics": metrics,
            "stage": stage,
            "recent_events": recent_events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# UNIVERSAL EXPLORER ENDPOINTS
# ============================================================================


@router.get("/knowledge/graph")
async def get_knowledge_graph():
    """Get knowledge graph data for visualization"""
    try:
        # Get all concepts with relationships
        concepts = await state.cognitive_core.semantic_memory.get_all_concepts(100)
        
        nodes = []
        edges = []
        node_ids = set()
        
        for concept in concepts:
            concept_name = concept.get("concept", "")
            if concept_name and concept_name not in node_ids:
                nodes.append({
                    "id": concept_name,
                    "label": concept_name.title(),
                    "strength": concept.get("strength", 1),
                    "definition": concept.get("definition", "")[:100]
                })
                node_ids.add(concept_name)
                
                # Add relationships as edges
                for rel in concept.get("relationships", []):
                    if rel and rel != concept_name:
                        edges.append({
                            "source": concept_name,
                            "target": rel.lower(),
                            "type": "related"
                        })
        
        # Get insights as special nodes
        insights = await state.cognitive_core.philosophical_memory.get_insights(20)
        for i, insight in enumerate(insights):
            insight_id = f"insight_{i}"
            nodes.append({
                "id": insight_id,
                "label": f"💡 Insight {i+1}",
                "strength": insight.get("wisdom_level", 1),
                "definition": insight.get("insight", "")[:100],
                "type": "insight"
            })
        
        return {
            "nodes": nodes,
            "edges": edges,
            "stats": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "concepts": len([n for n in nodes if n.get("type") != "insight"]),
                "insights": len([n for n in nodes if n.get("type") == "insight"])
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXPORT/IMPORT MEMORY ENDPOINTS
# ============================================================================

@router.get("/memory/export")
async def export_memory():
    """Export AI's memory and knowledge"""
    try:
        # Gather all memory data
        concepts = await state.cognitive_core.semantic_memory.get_all_concepts(500)
        episodes = await state.cognitive_core.episodic_memory.recall_recent_episodes(100)
        insights = await state.cognitive_core.philosophical_memory.get_insights(100)
        questions = await state.cognitive_core.philosophical_memory.get_unanswered_questions(100)
        metrics = await state.cognitive_core.growth_tracker.calculate_metrics()
        stage = await state.cognitive_core.growth_tracker.get_current_stage()
        
        export_data = {
            "version": "1.0",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "growth_stage": stage,
            "metrics": metrics,
            "semantic_memory": concepts,
            "episodic_memory": episodes,
            "insights": insights,
            "questions": questions
        }
        
        return export_data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class MemoryImport(BaseModel):
    semantic_memory: Optional[List[Dict]] = None
    insights: Optional[List[Dict]] = None

@router.post("/memory/import")
async def import_memory(data: MemoryImport):
    """Import memory data"""
    try:
        imported = {"concepts": 0, "insights": 0}
        
        # Import semantic memory
        if data.semantic_memory:
            for concept in data.semantic_memory:
                if concept.get("concept"):
                    await state.cognitive_core.semantic_memory.store_concept(
                        concept=concept.get("concept"),
                        definition=concept.get("definition", ""),
                        relationships=concept.get("relationships", []),
                        metadata=concept.get("metadata", {})
                    )
                    imported["concepts"] += 1
        
        # Import insights
        if data.insights:
            for insight in data.insights:
                if insight.get("insight"):
                    await state.cognitive_core.philosophical_memory.store_insight(
                        insight=insight.get("insight"),
                        wisdom_level=insight.get("wisdom_level", 1)
                    )
                    imported["insights"] += 1
        
        return {"status": "success", "imported": imported}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# EXPORT CONVERSATIONS ENDPOINTS
# ============================================================================

@router.get("/chat/export/{session_id}")
async def export_conversation(session_id: str, format: str = "markdown"):
    """Export conversation as markdown or JSON"""
    try:
        history = await get_conversation_history(session_id, limit=500)
        
        if format == "json":
            return {
                "session_id": session_id,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "messages": history
            }
        
        # Markdown format
        md_content = f"# Quantum AI Conversation\n\n"
        md_content += f"**Session:** {session_id}\n"
        md_content += f"**Exported:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}\n\n"
        md_content += "---\n\n"
        
        for msg in history:
            role = "**You:**" if msg.get("role") == "user" else "**Quantum AI:**"
            content = msg.get("content", "")
            timestamp = msg.get("timestamp", "")[:19] if msg.get("timestamp") else ""
            md_content += f"{role}\n{content}\n\n"
        
        return {"markdown": md_content, "session_id": session_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/settings/statistics")
async def get_settings_statistics():
    """Get application statistics for Settings panel"""
    try:
        # Total chat conversations (unique session_ids)
        session_ids = await state.db.chat_messages.distinct("session_id")
        total_conversations = len(session_ids)
        # Total messages sent
        total_messages = await state.db.chat_messages.count_documents({})
        # Users: single-user system
        users = 1
        # Growth events recorded
        growth_events = await state.db.growth_metrics.count_documents({})
        return {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "users": users,
            "growth_events": growth_events
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
