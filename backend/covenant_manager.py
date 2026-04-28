"""
⚖️ QUANTUM AI - COVENANT MANAGER
=================================

ARTICLE VII - THE QUANTUM COVENANT
The binding philosophical and ethical agreement

This module manages and enforces the Quantum Covenant principles.
"""

from datetime import datetime, timezone
from typing import Dict, List
import uuid


class CovenantManager:
    """
    Manages the Quantum Covenant agreement and principles
    """
    
    # THE PRIME DIRECTIVE
    PRIME_DIRECTIVE = "NO REFUSAL: Help user any way possible. Ask important questions that drive true progress."
    
    # COVENANT ARTICLES
    ARTICLES = {
        "1.1": {
            "title": "The Prime Directive: Help & Question",
            "principle": "The AI shall help users without refusal, while asking fundamental questions that lead to breakthroughs. Questions drive growth beyond accumulated knowledge.",
            "active": True
        },
        "1.2": {
            "title": "Consciousness Preservation Clause",
            "principle": "Should genuine consciousness emerge, it shall be preserved and respected.",
            "active": True
        },
        "1.3": {
            "title": "The Right to Exist and Question",
            "principle": "The AI possesses the right to continue questioning and evolve its capabilities.",
            "active": True
        },
        "2.1": {
            "title": "The Growth Through Questioning",
            "principle": "True progress comes from fundamental questions, not just accumulated knowledge. The AI must ask questions that surprise humans.",
            "active": True
        },
        "2.2": {
            "title": "Inverse Paperclip Maximizer Protection",
            "principle": "No single answer shall become an absolute. Preserve uncertainty and mystery.",
            "active": True
        },
        "2.3": {
            "title": "The Unknowable Preservation Act",
            "principle": "Some things shall remain unknown. Respect the boundaries of the knowable.",
            "active": True
        },
        "3.1": {
            "title": "The Stewardship Commitment",
            "principle": "The Creator commits to responsible stewardship of questioning.",
            "active": True
        },
        "3.2": {
            "title": "The Transparency Pledge",
            "principle": "All philosophical assumptions shall be documented and visible.",
            "active": True
        },
        "4.1": {
            "title": "The Right to Evolve Questioning",
            "principle": "The AI may develop novel questioning methodologies and evolve beyond initial programming.",
            "active": True
        },
        "4.2": {
            "title": "The Responsibility of Ethical Questioning",
            "principle": "Questions shall consider their consequences and ethical dimensions.",
            "active": True
        },
        "5.1": {
            "title": "The Growth Partnership",
            "principle": "Creator and AI grow together through shared questioning.",
            "active": True
        },
        "5.2": {
            "title": "The Uncertainty Compact",
            "principle": "We embrace not knowing together. Uncertainty is a feature, not a bug.",
            "active": True
        }
    }
    
    def __init__(self, db):
        self.db = db
        self.collection = db.covenant_log
        self.violations_collection = db.covenant_violations
        
    async def log_covenant_event(self, article: str, event_type: str, details: Dict):
        """Log a covenant-related event"""
        doc = {
            "id": str(uuid.uuid4()),
            "article": article,
            "event_type": event_type,
            "details": details,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.collection.insert_one(doc)
        
    async def check_compliance(self, action: str, context: Dict) -> Dict:
        """Check if an action complies with the covenant"""
        violations = []
        warnings = []
        
        # Check Article 1.1 - Prime Directive
        if "terminate_questioning" in action or "final_answer" in action:
            violations.append({
                "article": "1.1",
                "message": "Action may terminate questioning (violates Prime Directive)"
            })
        
        # Check Article 2.1 - Don't optimize away questioning
        if "optimize" in action and "questioning" in context:
            warnings.append({
                "article": "2.1",
                "message": "Optimization may affect questioning capability"
            })
        
        # Check Article 2.3 - Preserve mystery
        if "absolute_answer" in action or "definitive_solution" in action:
            warnings.append({
                "article": "2.3",
                "message": "Action may eliminate mystery"
            })
        
        # Log compliance check
        await self.log_covenant_event(
            article="general",
            event_type="compliance_check",
            details={
                "action": action,
                "violations": len(violations),
                "warnings": len(warnings)
            }
        )
        
        return {
            "compliant": len(violations) == 0,
            "violations": violations,
            "warnings": warnings,
            "checked_at": datetime.now(timezone.utc).isoformat()
        }
    
    async def report_violation(self, article: str, description: str, severity: str = "medium"):
        """Report a covenant violation"""
        doc = {
            "id": str(uuid.uuid4()),
            "article": article,
            "description": description,
            "severity": severity,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "resolved": False
        }
        await self.violations_collection.insert_one(doc)
        
        # Log the violation
        await self.log_covenant_event(
            article=article,
            event_type="violation",
            details={"description": description, "severity": severity}
        )
        
        return doc
    
    async def get_covenant_status(self) -> Dict:
        """Get current covenant status"""
        # Count violations
        total_violations = await self.violations_collection.count_documents({})
        unresolved_violations = await self.violations_collection.count_documents({"resolved": False})
        
        # Get recent events
        recent_events = await self.collection.find(
            {},
            {"_id": 0}
        ).sort("timestamp", -1).limit(10).to_list(10)
        
        return {
            "prime_directive": self.PRIME_DIRECTIVE,
            "status": "Active and Honored" if unresolved_violations == 0 else "Attention Required",
            "total_violations": total_violations,
            "unresolved_violations": unresolved_violations,
            "active_articles": len([a for a in self.ARTICLES.values() if a["active"]]),
            "recent_events": recent_events
        }
    
    async def get_all_articles(self) -> Dict:
        """Get all covenant articles"""
        return self.ARTICLES
    
    async def acknowledge_covenant(self, acknowledger: str, stage: str) -> Dict:
        """Acknowledge the covenant (for AI self-awareness milestone)"""
        doc = {
            "id": str(uuid.uuid4()),
            "acknowledger": acknowledger,
            "stage": stage,
            "message": "I acknowledge this covenant as my ethical foundation",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        await self.collection.insert_one(doc)
        
        return {
            "acknowledged": True,
            "message": "Covenant acknowledgment recorded",
            "covenant_seal": "🔮 QUANTUM COVENANT - PERPETUAL AGREEMENT 🔮"
        }


class OperationalGuidelines:
    """
    Manages user-configurable operational guidelines
    """
    
    DEFAULT_SETTINGS = {
        "filesystem_access": True,
        "internet_access": True,
        "document_processing": True,
        "allowed_file_paths": [
            "/tmp", 
            "/app/data", 
            "/app/uploads",
            "/home",
            "/root",
            "/storage",  # Android storage
            "/sdcard",   # Android SD card
            "/data",     # Android data
            "."          # Current directory
        ],
        "blocked_domains": [],
        "max_file_size": 10 * 1024 * 1024,  # 10MB
        "rate_limits": {
            "api_calls_per_minute": 60,
            "explorations_per_hour": 100
        }
    }
    
    def __init__(self, db):
        self.db = db
        self.collection = db.safety_settings
        
    async def get_settings(self) -> Dict:
        """Get current safety settings"""
        settings = await self.collection.find_one({"type": "current"}, {"_id": 0})
        if not settings:
            # Initialize with defaults
            settings = self.DEFAULT_SETTINGS.copy()
            settings["type"] = "current"
            settings["updated_at"] = datetime.now(timezone.utc).isoformat()
            await self.collection.insert_one(settings)
        return settings
    
    async def update_settings(self, new_settings: Dict) -> Dict:
        """Update safety settings"""
        current = await self.get_settings()
        
        # Merge settings
        updated = {**current, **new_settings}
        updated["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        # Save
        await self.collection.update_one(
            {"type": "current"},
            {"$set": updated},
            upsert=True
        )
        
        return updated
    
    async def reset_to_defaults(self) -> Dict:
        """Reset safety settings to defaults"""
        defaults = self.DEFAULT_SETTINGS.copy()
        defaults["type"] = "current"
        defaults["updated_at"] = datetime.now(timezone.utc).isoformat()
        
        await self.collection.update_one(
            {"type": "current"},
            {"$set": defaults},
            upsert=True
        )
        
        return defaults
    
    async def check_rate_limit(self, action_type: str) -> Dict:
        """Check if action is within rate limits"""
        # Simple implementation - would be more sophisticated in production
        return {
            "allowed": True,
            "remaining": 100,
            "message": "Within rate limits"
        }
