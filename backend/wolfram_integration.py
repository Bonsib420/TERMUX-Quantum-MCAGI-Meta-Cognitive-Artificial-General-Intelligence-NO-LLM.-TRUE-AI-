"""
🔬 Wolfram Alpha Integration
Mathematical and scientific knowledge engine for Quantum AI
"""

import wolframalpha
import os
from typing import Dict, Optional, List


class WolframEngine:
    """
    Wolfram Alpha integration for mathematical and scientific queries.
    Provides computational knowledge that no LLM can match.
    """
    
    def __init__(self, app_id: str = None):
        self.app_id = app_id or os.environ.get('WOLFRAM_APP_ID', 'A24U8GXLAU')
        self.client = wolframalpha.Client(self.app_id)
        self.query_history = []
        
    def query(self, question: str) -> Dict:
        """
        Query Wolfram Alpha and return structured results.
        """
        try:
            question = question.replace("×", "*").replace("÷", "/")
            res = self.client.query(question)
            
            results = {
                'success': res.success,
                'query': question,
                'pods': [],
                'primary_result': None,
                'images': []
            }
            
            for pod in res.pods:
                pod_data = {
                    'title': pod.title,
                    'texts': [],
                    'images': []
                }
                
                for sub in pod.subpods:
                    if hasattr(sub, 'plaintext') and sub.plaintext:
                        pod_data['texts'].append(sub.plaintext)
                    if hasattr(sub, 'img') and sub.img:
                        pod_data['images'].append(sub.img.src)
                        results['images'].append(sub.img.src)
                
                results['pods'].append(pod_data)
                
                # Get primary result
                if pod.primary and pod_data['texts']:
                    results['primary_result'] = pod_data['texts'][0]
            
            # Store in history
            self.query_history.append({
                'query': question,
                'success': res.success,
                'result': results['primary_result']
            })
            
            return results
            
        except Exception as e:
            return {
                'success': False,
                'query': question,
                'error': str(e),
                'pods': [],
                'primary_result': None
            }
    
    def get_math_result(self, expression: str) -> Optional[str]:
        """Get mathematical computation result"""
        result = self.query(expression)
        return result.get('primary_result')
    
    def get_scientific_fact(self, topic: str) -> Dict:
        """Get scientific information about a topic"""
        result = self.query(topic)
        
        facts = []
        for pod in result.get('pods', []):
            for text in pod.get('texts', []):
                if text and len(text) > 10:
                    facts.append({
                        'category': pod['title'],
                        'fact': text
                    })
        
        return {
            'topic': topic,
            'facts': facts[:5],  # Top 5 facts
            'primary': result.get('primary_result'),
            'images': result.get('images', [])[:3]
        }
    
    def solve_equation(self, equation: str) -> Dict:
        """Solve a mathematical equation"""
        result = self.query(f"solve {equation}")
        
        solutions = []
        for pod in result.get('pods', []):
            if 'solution' in pod['title'].lower() or 'result' in pod['title'].lower():
                solutions.extend(pod.get('texts', []))
        
        return {
            'equation': equation,
            'solutions': solutions,
            'steps': [p['texts'] for p in result.get('pods', []) if 'step' in p['title'].lower()]
        }
    
    def get_definition(self, word: str) -> Dict:
        """Get definition and etymology"""
        result = self.query(f"define {word}")
        
        definitions = []
        etymology = None
        
        for pod in result.get('pods', []):
            if 'definition' in pod['title'].lower():
                definitions.extend(pod.get('texts', []))
            if 'etymology' in pod['title'].lower():
                etymology = pod.get('texts', [None])[0]
        
        return {
            'word': word,
            'definitions': definitions,
            'etymology': etymology
        }
    
    def quantum_physics_query(self, query: str) -> Dict:
        """Specialized quantum physics queries"""
        result = self.query(f"quantum physics {query}")
        return {
            'query': query,
            'result': result.get('primary_result'),
            'all_info': result.get('pods', [])
        }
    
    def get_query_history(self) -> List[Dict]:
        """Get recent query history"""
        return self.query_history[-20:]


# Global instance
_wolfram_engine = None

def get_wolfram_engine() -> WolframEngine:
    """Get or create Wolfram engine instance"""
    global _wolfram_engine
    if _wolfram_engine is None:
        _wolfram_engine = WolframEngine()
    return _wolfram_engine
