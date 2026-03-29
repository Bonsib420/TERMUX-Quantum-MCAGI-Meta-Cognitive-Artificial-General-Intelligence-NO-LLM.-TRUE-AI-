"""
Wolfram Cloud — save/load Quantum MCAGI state
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
        # Convert any datetime objects to ISO strings for JSON serialization
        def serialize_dates(obj):
            if isinstance(obj, dict):
                return {k: serialize_dates(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [serialize_dates(v) for v in obj]
            elif isinstance(obj, datetime):
                return obj.isoformat()
            return obj
        data_serializable = serialize_dates(data)
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
