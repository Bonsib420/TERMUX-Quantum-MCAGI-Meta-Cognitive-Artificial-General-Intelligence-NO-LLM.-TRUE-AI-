"""
📚 QUANTUM AI - DICTIONARY INTEGRATION
======================================

Downloads and integrates comprehensive dictionaries into the semantic memory.

Sources:
1. WordNet - Lexical database with semantic relationships
2. Free Dictionary API - Online definitions and examples
3. ConceptNet - Semantic knowledge graph

ARTICLE 1.1 - Prime Directive: Build understanding through knowledge
"""

import nltk
import requests
from typing import Dict, List, Optional
import asyncio
import json


class WordNetDictionary:
    """
    WordNet integration - comprehensive English lexical database
    """
    
    def __init__(self):
        self.initialized = False
        
    def initialize(self):
        """Download WordNet data"""
        try:
            print("📥 Downloading WordNet dictionary...")
            nltk.download('wordnet', quiet=True)
            nltk.download('omw-1.4', quiet=True)  # Open Multilingual WordNet
            from nltk.corpus import wordnet as wn
            self.wn = wn
            self.initialized = True
            print("✅ WordNet downloaded successfully")
            return True
        except Exception as e:
            print(f"❌ WordNet download failed: {str(e)}")
            return False
    
    def get_definition(self, word: str) -> Dict:
        """Get comprehensive word definition from WordNet"""
        if not self.initialized:
            if not self.initialize():
                return None
        
        try:
            synsets = self.wn.synsets(word)
            
            if not synsets:
                return None
            
            definitions = []
            examples = []
            synonyms = set()
            antonyms = set()
            hypernyms = []  # More general terms
            hyponyms = []   # More specific terms
            
            for synset in synsets:
                # Definitions
                definitions.append({
                    "definition": synset.definition(),
                    "part_of_speech": synset.pos(),
                    "name": synset.name()
                })
                
                # Examples
                for example in synset.examples():
                    examples.append(example)
                
                # Synonyms
                for lemma in synset.lemmas():
                    synonyms.add(lemma.name().replace('_', ' '))
                    
                    # Antonyms
                    if lemma.antonyms():
                        for ant in lemma.antonyms():
                            antonyms.add(ant.name().replace('_', ' '))
                
                # Hypernyms (broader concepts)
                for hyper in synset.hypernyms():
                    hypernyms.append(hyper.name().split('.')[0].replace('_', ' '))
                
                # Hyponyms (narrower concepts)
                for hypo in synset.hyponyms()[:5]:  # Limit to 5
                    hyponyms.append(hypo.name().split('.')[0].replace('_', ' '))
            
            return {
                "word": word,
                "definitions": definitions,
                "examples": examples,
                "synonyms": list(synonyms),
                "antonyms": list(antonyms),
                "hypernyms": list(set(hypernyms)),  # More general
                "hyponyms": list(set(hyponyms)),    # More specific
                "source": "WordNet"
            }
            
        except Exception as e:
            print(f"Error getting WordNet definition: {str(e)}")
            return None


class FreeDictionaryAPI:
    """
    Free Dictionary API integration - online definitions
    """
    
    BASE_URL = "https://api.dictionaryapi.dev/api/v2/entries/en/"
    
    def get_definition(self, word: str) -> Dict:
        """Get definition from Free Dictionary API"""
        try:
            response = requests.get(f"{self.BASE_URL}{word}", timeout=10)
            
            if response.status_code != 200:
                return None
            
            data = response.json()
            if not data:
                return None
            
            entry = data[0]
            
            definitions = []
            examples = []
            synonyms = set()
            antonyms = set()
            
            for meaning in entry.get('meanings', []):
                pos = meaning.get('partOfSpeech', 'unknown')
                
                for definition in meaning.get('definitions', []):
                    definitions.append({
                        "definition": definition.get('definition', ''),
                        "part_of_speech": pos,
                        "example": definition.get('example', '')
                    })
                    
                    if definition.get('example'):
                        examples.append(definition['example'])
                    
                    # Synonyms and antonyms
                    for syn in definition.get('synonyms', []):
                        synonyms.add(syn)
                    for ant in definition.get('antonyms', []):
                        antonyms.add(ant)
            
            return {
                "word": word,
                "phonetic": entry.get('phonetic', ''),
                "definitions": definitions,
                "examples": examples,
                "synonyms": list(synonyms),
                "antonyms": list(antonyms),
                "source": "Free Dictionary API"
            }
            
        except Exception as e:
            print(f"Error getting API definition: {str(e)}")
            return None


class DictionaryIntegration:
    """
    Main dictionary integration for Quantum AI
    Combines multiple sources for comprehensive definitions
    """
    
    def __init__(self, semantic_memory):
        self.semantic_memory = semantic_memory
        self.wordnet = WordNetDictionary()
        self.free_dict = FreeDictionaryAPI()
        
    async def lookup_and_store(self, word: str) -> Dict:
        """
        Look up word in dictionaries and store in semantic memory
        """
        word = word.lower().strip()
        
        # Check if already in memory
        existing = await self.semantic_memory.recall_concept(word)
        if existing:
            return {
                "word": word,
                "status": "already_exists",
                "data": existing
            }
        
        # Try WordNet first
        wordnet_data = self.wordnet.get_definition(word)
        
        # Try Free Dictionary API
        api_data = self.free_dict.get_definition(word)
        
        # Combine data
        combined = self._combine_definitions(word, wordnet_data, api_data)
        
        if not combined:
            return {
                "word": word,
                "status": "not_found",
                "data": None
            }
        
        # Store in semantic memory
        await self.semantic_memory.store_concept(
            concept=word,
            definition=combined["primary_definition"],
            relationships=combined["related_words"],
            metadata=combined
        )
        
        return {
            "word": word,
            "status": "added",
            "data": combined
        }
    
    def _combine_definitions(self, word: str, wordnet_data: Optional[Dict], api_data: Optional[Dict]) -> Optional[Dict]:
        """Combine definitions from multiple sources"""
        if not wordnet_data and not api_data:
            return None
        
        combined = {
            "word": word,
            "primary_definition": "",
            "all_definitions": [],
            "examples": [],
            "synonyms": set(),
            "antonyms": set(),
            "related_words": [],
            "sources": []
        }
        
        # WordNet data
        if wordnet_data:
            combined["sources"].append("WordNet")
            if wordnet_data["definitions"]:
                combined["primary_definition"] = wordnet_data["definitions"][0]["definition"]
                combined["all_definitions"].extend([d["definition"] for d in wordnet_data["definitions"]])
            
            combined["examples"].extend(wordnet_data["examples"])
            combined["synonyms"].update(wordnet_data["synonyms"])
            combined["antonyms"].update(wordnet_data["antonyms"])
            
            # Add related words
            combined["related_words"].extend(wordnet_data["synonyms"][:5])
            combined["related_words"].extend(wordnet_data["hypernyms"][:3])
            combined["related_words"].extend(wordnet_data["hyponyms"][:3])
        
        # API data
        if api_data:
            combined["sources"].append("Free Dictionary API")
            if not combined["primary_definition"] and api_data["definitions"]:
                combined["primary_definition"] = api_data["definitions"][0]["definition"]
            
            combined["all_definitions"].extend([d["definition"] for d in api_data["definitions"]])
            combined["examples"].extend(api_data["examples"])
            combined["synonyms"].update(api_data["synonyms"])
            combined["antonyms"].update(api_data["antonyms"])
            combined["related_words"].extend(api_data["synonyms"][:5])
        
        # Convert sets to lists
        combined["synonyms"] = list(combined["synonyms"])
        combined["antonyms"] = list(combined["antonyms"])
        combined["related_words"] = list(set(combined["related_words"]))[:20]  # Limit
        
        return combined
    
    async def batch_load_common_words(self, limit: int = 100) -> Dict:
        """
        Load common English words into the dictionary
        """
        # Common words list (you can expand this)
        common_words = [
            # Abstract concepts
            "consciousness", "intelligence", "understanding", "knowledge", "wisdom",
            "awareness", "perception", "reality", "existence", "truth", "meaning",
            "purpose", "identity", "self", "mind", "thought", "idea", "concept",
            
            # Emotions
            "love", "fear", "joy", "sadness", "anger", "hope", "curiosity",
            "wonder", "awe", "compassion", "empathy",
            
            # Actions
            "think", "learn", "understand", "question", "explore", "discover",
            "create", "imagine", "remember", "forget", "know", "believe",
            
            # Qualities
            "good", "bad", "true", "false", "right", "wrong", "beautiful",
            "ugly", "simple", "complex", "deep", "shallow",
            
            # Science
            "energy", "matter", "time", "space", "universe", "quantum",
            "particle", "wave", "force", "field",
            
            # Philosophy
            "ethics", "morality", "virtue", "justice", "freedom", "responsibility",
            "choice", "will", "determinism", "causality"
        ]
        
        results = {
            "total": len(common_words[:limit]),
            "added": 0,
            "already_exists": 0,
            "not_found": 0,
            "failed": 0
        }
        
        for word in common_words[:limit]:
            try:
                result = await self.lookup_and_store(word)
                
                if result["status"] == "added":
                    results["added"] += 1
                elif result["status"] == "already_exists":
                    results["already_exists"] += 1
                elif result["status"] == "not_found":
                    results["not_found"] += 1
                
                # Small delay to be respectful to API
                await asyncio.sleep(0.1)
                
            except Exception as e:
                results["failed"] += 1
                print(f"Failed to load '{word}': {str(e)}")
        
        return results


# Singleton instance
_dictionary_integration = None

def get_dictionary_integration(semantic_memory):
    """Get or create dictionary integration instance"""
    global _dictionary_integration
    
    if _dictionary_integration is None:
        _dictionary_integration = DictionaryIntegration(semantic_memory)
    
    return _dictionary_integration
