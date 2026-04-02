"""
🔬 Enhanced WolframAlpha Integration
====================================
Full WolframAlpha Pro integration with:
- Step-by-step solutions
- Full result data
- Spoken results
- Image/plot retrieval
- Conversation mode
"""

import os
import re
import requests
import logging
from typing import Dict, List, Optional, Any
import xml.etree.ElementTree as ET

logger = logging.getLogger("quantum_ai")


class EnhancedWolframAlpha:
    """
    Enhanced WolframAlpha integration with Pro features.
    
    Features:
    - Full API with complete pod data
    - Step-by-step solutions
    - Spoken results (audio)
    - Conversation mode
    - Image/plot extraction
    """
    
    def __init__(self, app_id: str = None):
        self.app_id = app_id or os.environ.get('WOLFRAM_APPID', 'A24U8GXLAU')
        self.base_url = "http://api.wolframalpha.com/v2/query"
        self.short_url = "http://api.wolframalpha.com/v1/result"
        self.spoken_url = "http://api.wolframalpha.com/v1/spoken"
        self.conversation_url = "http://api.wolframalpha.com/v1/conversation.jsp"
        
        self.queries_made = 0
        self.cache = {}
        self.conversation_id = None
        self.conversation_host = None
        
        logger.info("Enhanced WolframAlpha initialized")
    
    def query_full(self, question: str, include_pods: List[str] = None) -> Dict:
        """
        Full API query with complete results.
        
        Args:
            question: The query string
            include_pods: Optional list of pod IDs to include
        
        Returns:
            Dict with all pods, images, and data
        """
        params = {
            'input': question,
            'appid': self.app_id,
            'format': 'plaintext,image',
            'output': 'json',
            'podstate': 'Step-by-step solution'  # Request step-by-step for Pro
        }
        
        if include_pods:
            params['includepodid'] = ','.join(include_pods)
        
        try:
            response = requests.get(self.base_url, params=params, timeout=30)
            self.queries_made += 1
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_full_response(data)
            else:
                return {'error': f'HTTP {response.status_code}', 'success': False}
        except Exception as e:
            logger.error(f"WolframAlpha query failed: {e}")
            return {'error': str(e), 'success': False}
    
    def _parse_full_response(self, data: Dict) -> Dict:
        """Parse full API response into structured format."""
        query_result = data.get('queryresult', {})
        
        result = {
            'success': query_result.get('success', False),
            'input_interpretation': None,
            'primary_result': None,
            'pods': [],
            'images': [],
            'step_by_step': None,
            'related_queries': [],
            'raw_data': query_result
        }
        
        pods = query_result.get('pods', [])
        
        for pod in pods:
            pod_id = pod.get('id', '')
            pod_title = pod.get('title', '')
            subpods = pod.get('subpods', [])
            
            pod_data = {
                'id': pod_id,
                'title': pod_title,
                'texts': [],
                'images': []
            }
            
            for subpod in subpods:
                # Text content
                plaintext = subpod.get('plaintext', '')
                if plaintext:
                    pod_data['texts'].append(plaintext)
                
                # Images
                img = subpod.get('img', {})
                if img:
                    pod_data['images'].append({
                        'src': img.get('src', ''),
                        'alt': img.get('alt', ''),
                        'title': img.get('title', '')
                    })
                    result['images'].append(img.get('src', ''))
            
            result['pods'].append(pod_data)
            
            # Extract specific pod types
            if pod_id == 'Input':
                result['input_interpretation'] = ' '.join(pod_data['texts'])
            elif pod.get('primary', False):
                result['primary_result'] = ' '.join(pod_data['texts'])
            elif 'step' in pod_title.lower() or 'solution' in pod_title.lower():
                result['step_by_step'] = '\n'.join(pod_data['texts'])
        
        # If no primary result, use first result pod
        if not result['primary_result'] and len(result['pods']) > 1:
            for pod in result['pods']:
                if pod['texts'] and pod['id'] != 'Input':
                    result['primary_result'] = pod['texts'][0]
                    break
        
        return result
    
    def query_simple(self, question: str) -> Optional[str]:
        """Simple query returning just the answer text."""
        cache_key = question.lower().strip()
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        params = {
            'i': question,
            'appid': self.app_id
        }
        
        try:
            response = requests.get(self.short_url, params=params, timeout=15)
            self.queries_made += 1
            
            if response.status_code == 200:
                text = response.text.strip()
                if "did not understand" not in text.lower():
                    self.cache[cache_key] = text
                    return text
            return None
        except Exception as e:
            logger.error(f"Simple query failed: {e}")
            return None
    
    def query_spoken(self, question: str) -> Optional[str]:
        """Get spoken/audio-friendly response."""
        params = {
            'i': question,
            'appid': self.app_id
        }
        
        try:
            response = requests.get(self.spoken_url, params=params, timeout=15)
            self.queries_made += 1
            
            if response.status_code == 200:
                return response.text.strip()
            return None
        except Exception as e:
            logger.error(f"Spoken query failed: {e}")
            return None
    
    def query_conversation(self, question: str) -> Dict:
        """
        Conversational query that maintains context.
        Useful for follow-up questions.
        """
        params = {
            'i': question,
            'appid': self.app_id
        }
        
        # Add conversation context if available
        if self.conversation_id:
            params['conversationid'] = self.conversation_id
        if self.conversation_host:
            params['host'] = self.conversation_host
        
        try:
            response = requests.get(self.conversation_url, params=params, timeout=15)
            self.queries_made += 1
            
            if response.status_code == 200:
                data = response.json()
                
                # Update conversation state
                self.conversation_id = data.get('conversationID')
                self.conversation_host = data.get('host')
                
                return {
                    'success': True,
                    'result': data.get('result', ''),
                    'conversation_id': self.conversation_id,
                    'followup_query': data.get('followup', {}).get('query', ''),
                    'raw': data
                }
            return {'success': False, 'error': f'HTTP {response.status_code}'}
        except Exception as e:
            logger.error(f"Conversation query failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def reset_conversation(self):
        """Reset conversation context."""
        self.conversation_id = None
        self.conversation_host = None
    
    def query_step_by_step(self, question: str) -> Dict:
        """
        Query with emphasis on getting step-by-step solutions.
        Best for math problems.
        """
        result = self.query_full(question)
        
        if result.get('step_by_step'):
            return {
                'success': True,
                'steps': result['step_by_step'],
                'primary_result': result.get('primary_result'),
                'images': result.get('images', [])
            }
        elif result.get('primary_result'):
            return {
                'success': True,
                'steps': None,
                'primary_result': result['primary_result'],
                'images': result.get('images', [])
            }
        else:
            return {
                'success': False,
                'error': 'No solution found'
            }
    
    def is_factual_query(self, text: str) -> bool:
        """Detect if this is a query WolframAlpha can answer."""
        t = text.lower()
        
        # Contains numbers or math
        if re.search(r'\d', t):
            return True
        
        # Math keywords
        math_keywords = [
            'calculate', 'compute', 'solve', 'integrate', 'derivative',
            'equation', 'formula', 'factor', 'simplify', 'expand',
            'limit', 'sum', 'product', 'matrix', 'vector'
        ]
        if any(kw in t for kw in math_keywords):
            return True
        
        # Science/factual keywords
        factual_keywords = [
            'how many', 'what is the', 'distance', 'population',
            'weather', 'convert', 'temperature', 'mass', 'speed',
            'height', 'weight', 'calories', 'nutrition',
            'stock', 'price', 'exchange rate', 'currency'
        ]
        if any(kw in t for kw in factual_keywords):
            return True
        
        # Astronomy
        astro_keywords = [
            'planet', 'star', 'moon', 'sun', 'galaxy', 'light year',
            'orbit', 'asteroid', 'comet', 'constellation'
        ]
        if any(kw in t for kw in astro_keywords):
            return True
        
        return False
    
    def get_status(self) -> Dict:
        """Get WolframAlpha status."""
        return {
            'available': True,
            'app_id_configured': self.app_id != 'T7PA7A-E38RXXXXX',
            'queries_made': self.queries_made,
            'cache_size': len(self.cache),
            'conversation_active': self.conversation_id is not None,
            'endpoints': {
                'full': self.base_url,
                'simple': self.short_url,
                'spoken': self.spoken_url,
                'conversation': self.conversation_url
            }
        }


# Singleton instance
_wolfram_engine = None

def get_wolfram_engine() -> EnhancedWolframAlpha:
    """Get or create the WolframAlpha engine."""
    global _wolfram_engine
    if _wolfram_engine is None:
        _wolfram_engine = EnhancedWolframAlpha()
    return _wolfram_engine
