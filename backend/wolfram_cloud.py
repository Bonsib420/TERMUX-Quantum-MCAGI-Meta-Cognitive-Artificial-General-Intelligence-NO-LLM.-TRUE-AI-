"""
Wolfram Cloud — save/load Quantum MCAGI state

Cloud path structure (designed for future multi-user/multi-node growth):
  QuantumMCAGI/state          — core memory (growth, concepts, session_state)
  QuantumMCAGI/brain          — full brain snapshot (research + dreams + concepts)
  QuantumMCAGI/research/{id}  — individual research sessions (future)
  QuantumMCAGI/nodes/{node}   — per-node state for distributed expansion (future)

The cloud is the brain; the app/website is the window into it.
"""
import json
from datetime import datetime

def get_cloud_session():
    """get_cloud_session - Auto-documented by self-evolution."""
    from wolframclient.evaluation import WolframCloudSession, SecuredAuthenticationKey
    from wolframclient.language import wl
    sak = SecuredAuthenticationKey(
        'XQFcaGYqlxKynDG/OnScZgYiVue2HLfDJkBwiLDl1gw=',
        'gsJeEwTtCBrOJOojWWFLlR2yrwszXJfzBI8mFco/Q1U=')
    session = WolframCloudSession(credentials=sak)
    session.start()
    return session

def _serialize_dates(obj):
    """Recursively convert datetime objects to ISO strings for JSON."""
    if isinstance(obj, dict):
        return {k: _serialize_dates(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_serialize_dates(v) for v in obj]
    elif isinstance(obj, datetime):
        return obj.isoformat()
    return obj

def cloud_save(memory):
    """cloud_save - Auto-documented by self-evolution."""
    try:
        from wolframclient.language import wl
        session = get_cloud_session()
        data = {
            'growth': memory.growth,
            'concepts': memory.concepts,
            'session_state': memory.session_state,
        }
        data_serializable = _serialize_dates(data)
        session.evaluate(wl.CloudPut(json.dumps(data_serializable), 'QuantumMCAGI/state'))
        session.stop()
        return True
    except Exception as e:
        print(f"  Cloud error: {e}")
        return False

def cloud_load():
    """cloud_load - Auto-documented by self-evolution."""
    try:
        from wolframclient.language import wl
        session = get_cloud_session()
        raw = session.evaluate(wl.CloudGet('QuantumMCAGI/state'))
        session.stop()
        if raw:
            return json.loads(raw)
    except Exception as e:
        print(f"  Cloud error: {e}")
    return None

def cloud_status():
    """cloud_status - Auto-documented by self-evolution."""
    try:
        from wolframclient.language import wl
        session = get_cloud_session()
        objects = session.evaluate(wl.CloudObjects('QuantumMCAGI/*'))
        session.stop()
        return objects
    except Exception as e:
        return f"Error: {e}"


# ── Autonomous brain sync (called by dream engine) ──────────────────────────

def cloud_save_brain(cognitive_core, dream_engine=None):
    """
    Save full brain snapshot to cloud — called autonomously by dream engine.
    Includes research insights, dream history, concept network stats.
    
    Cloud path: QuantumMCAGI/brain
    """
    try:
        from wolframclient.language import wl
        session = get_cloud_session()
        
        brain_data = {
            'saved_at': datetime.now().isoformat(),
            'version': '2.0',
        }
        
        # Cognitive core stats
        if cognitive_core:
            try:
                stats = cognitive_core.get_growth_stats() if hasattr(cognitive_core, 'get_growth_stats') else {}
                brain_data['growth_stats'] = _serialize_dates(stats)
            except Exception:
                brain_data['growth_stats'] = {}
        
        # Dream engine state
        if dream_engine:
            brain_data['dream_state'] = {
                'total_dreams': len(dream_engine.dream_log),
                'total_insights': len(dream_engine.insights_gained),
                'topics_explored': dream_engine.dream_topics[-50:],
                'recent_insights': [
                    {'type': i.get('type', ''), 'text': i.get('text', ''), 'at': i.get('discovered_at', '')}
                    for i in dream_engine.insights_gained[-20:]
                ],
            }
        
        session.evaluate(wl.CloudPut(json.dumps(brain_data), 'QuantumMCAGI/brain'))
        session.stop()
        return True
    except Exception as e:
        print(f"  Cloud brain save error: {e}")
        return False

def cloud_load_brain():
    """
    Load brain snapshot from cloud — for restoring state on startup
    or syncing across nodes.
    
    Cloud path: QuantumMCAGI/brain
    """
    try:
        from wolframclient.language import wl
        session = get_cloud_session()
        raw = session.evaluate(wl.CloudGet('QuantumMCAGI/brain'))
        session.stop()
        if raw:
            return json.loads(raw)
    except Exception as e:
        print(f"  Cloud brain load error: {e}")
    return None
