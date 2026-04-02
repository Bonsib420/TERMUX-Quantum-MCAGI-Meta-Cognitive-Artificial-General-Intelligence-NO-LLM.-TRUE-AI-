"""
🧠 QUANTUM AI - HIDDEN THINKING MODE
=====================================

ARTICLE 1.1 - Prime Directive: Question Everything (PRIVATELY)
ARTICLE 4.3 - Theory Building Stage

New Paradigm:
- User sees: Clean, confident conversation
- AI does: [Think → Question → Research → Synthesize → Respond]

UPGRADED: Now uses QuantumBrain as the TRUE AI
- Quantum Brain decides WHAT to say
- LLM only polishes grammar (if enabled)
- Integrity checking ensures meaning is preserved

This is the bridge between questioning AI and conversational AI.
"""

from typing import Dict, List, Optional
import re
from datetime import datetime, timezone
from hybrid_generator import create_hybrid_generator


class HiddenThinkingMode:
    """
    Internal thinking process - questions and research happen behind the scenes
    """
    
    def __init__(self, cognitive_core, dictionary, universal_explorer):
        self.cognitive_core = cognitive_core
        self.dictionary = dictionary
        self.universal_explorer = universal_explorer
        self.show_thinking = False  # User-controlled toggle
        
    async def process_with_thinking(self, user_input: str, context: Dict = None, conversation_history: List[Dict] = None, explain_mode: bool = False, structured_response: str = None) -> Dict:
        """
        Process input with hidden thinking mode
        
        Flow:
        1. Check if user is asking about uploaded files
        2. Detect unknowns
        3. Generate internal questions
        4. Self-research (including documents)
        5. Synthesize understanding
        6. Generate confident response (optionally weaving with structured_response via Markov)
        
        If explain_mode=True, includes detailed reasoning trace from QuantumBrain.
        """
        thinking_log = []
        
        # Store conversation history for context
        self.conversation_history = conversation_history or []
        
        # STEP 0: Check if user is asking about uploaded files
        document_context = await self._check_for_document_reference(user_input)
        if document_context:
            if self.show_thinking:
                thinking_log.append(f"📄 Detected question about: {document_context['filename']}")
        
        # STEP 0: WolframAlpha intercept for math/factual queries
        import re, httpx
        math_pattern = re.compile(r'[\d]+.*[\+\-\*\/\×\÷\^]|[\+\-\*\/\×\÷\^].*[\d]+')
        if math_pattern.search(user_input):
            try:
                clean_input = user_input.replace("×", "*").replace("÷", "/").replace("=", "")
                r = httpx.get(
                    "https://api.wolframalpha.com/v2/query",
                    params={"input": clean_input, "appid": "A24U8GXLAU", "format": "plaintext"},
                    timeout=8
                )
                import xml.etree.ElementTree as ET
                root = ET.fromstring(r.text)
                result = None
                for pod in root.findall("pod"):
                    if pod.get("primary") == "true" or pod.get("title") in ["Result", "Value", "Decimal approximation"]:
                        for sub in pod.findall("subpod"):
                            pt = sub.findtext("plaintext", "")
                            if pt:
                                result = pt
                                break
                    if result:
                        break
                if result:
                    response = f"The answer is: {result}"
                    return {
                        "response": response[0] if isinstance(response, tuple) else response,
                        "thinking_log": [],
                        "internal_questions": [],
                        "research_done": 1,
                        "confidence": 99,
                        "show_thinking": False,
                        "concepts": [],
                        "explanation": None
                    }
            except Exception as e:
                print(f"[STEP 0] WolframAlpha intercept failed: {e}")

        # STEP 1: Detect unknowns
        unknowns = await self._detect_unknowns(user_input)
        if self.show_thinking:
            thinking_log.append(f"🔍 Detected unknowns: {', '.join(unknowns[:3])}")
        
        # STEP 2: Generate internal questions (not shown to user)
        internal_questions = self._generate_internal_questions(user_input, unknowns)
        if self.show_thinking:
            thinking_log.append(f"❓ Internal questions: {internal_questions[0]}")
        
        # STEP 3: Self-research on unknowns (including documents)
        research_results = await self._self_research(unknowns, internal_questions, document_context)
        if self.show_thinking:
            thinking_log.append(f"📚 Research: {len(research_results)} sources found")
        
        # STEP 4: Synthesize understanding
        synthesized = await self._synthesize_understanding(user_input, research_results, document_context)
        if self.show_thinking:
            thinking_log.append(f"💡 Synthesized: {synthesized['confidence']}% confident")
        
        # STEP 5: Generate response (conversational, not questioning)
        response, explanation = await self._generate_confident_response(
            user_input, 
            synthesized,
            research_results,
            document_context,
            confusion_concepts=unknowns,
            explain_mode=explain_mode,
            structured_response=structured_response
        )
        
        # Store everything in memory (growth happens silently)
        await self._store_thinking_process(user_input, internal_questions, research_results)
        
        result = {
            "response": response,
            "thinking_log": thinking_log if self.show_thinking else [],
            "internal_questions": internal_questions,
            "research_done": len(research_results),
            "confidence": synthesized["confidence"],
            "show_thinking": self.show_thinking,
            "concepts": synthesized.get("concepts", [])
        }
        if explain_mode:
            result["explanation"] = explanation
        
        return result
    
    async def _check_for_document_reference(self, user_input: str) -> Optional[Dict]:
        """
        Check if user is asking about uploaded documents
        Supports MULTI-DOCUMENT context when user mentions multiple files
        Only triggers when user EXPLICITLY asks about documents
        """
        import os
        
        upload_dir = "/app/uploads"
        if not os.path.exists(upload_dir):
            return None
            
        all_files = [f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))]
        if not all_files:
            return None
        
        user_lower = user_input.lower()
        
        # Check for multi-document triggers - must be EXPLICIT
        multi_triggers = ['all documents', 'all files', 'both files', 'all my uploads', 'everything i uploaded', 'compare the documents', 'compare files']
        is_multi = any(trigger in user_lower for trigger in multi_triggers)
        
        # Check for single document triggers - must be EXPLICIT about documents
        # Removed 'this' as it's too generic and causes false positives
        single_triggers = [
            'the document', 'the pdf', 'the file i uploaded', 'my upload', 
            'uploaded file', 'uploaded document', 'what is in the file',
            'read the document', 'read the file', 'in my document',
            'from the document', 'from the file', 'from my upload',
            'about the document', 'about the file', 'summarize the document',
            'summarize the file', 'what does the document say', 'what does the file say'
        ]
        is_single = any(trigger in user_lower for trigger in single_triggers)
        
        # Check for specific filename mentions
        mentioned_files = []
        for f in all_files:
            fname_lower = f.lower().replace('.pdf', '').replace('.docx', '').replace('.txt', '')
            # Require at least 4 chars to match filename to avoid false positives
            if len(fname_lower) > 3 and (fname_lower in user_lower or f.lower() in user_lower):
                mentioned_files.append(f)
        
        if not (is_multi or is_single or mentioned_files):
            return None
        
        # Determine which files to process
        if mentioned_files:
            files_to_process = mentioned_files
        elif is_multi:
            # Process all document files (limit to 3 for context)
            priority_files = [f for f in all_files if f.endswith(('.pdf', '.docx', '.txt'))]
            files_to_process = sorted(priority_files, 
                                     key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), 
                                     reverse=True)[:3]
        else:
            # Single document - most recent
            priority_files = [f for f in all_files if f.endswith(('.pdf', '.docx', '.txt'))]
            files_to_check = priority_files if priority_files else all_files
            files_to_process = sorted(files_to_check, 
                                     key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), 
                                     reverse=True)[:1]
        
        if not files_to_process:
            return None
        
        # Process documents
        documents = []
        combined_text = ""
        
        for filename in files_to_process:
            file_path = os.path.join(upload_dir, filename)
            try:
                result = await self.universal_explorer.documents.process_document(file_path)
                if "error" not in result:
                    doc_text = result.get("text", "")
                    # Limit each document to 4000 chars for multi-doc, 8000 for single
                    max_chars = 4000 if len(files_to_process) > 1 else 8000
                    documents.append({
                        "filename": filename,
                        "path": file_path,
                        "text": doc_text[:max_chars],
                        "type": result.get("file_type", ""),
                        "pages": result.get("num_pages", 0)
                    })
                    combined_text += f"\n\n=== {filename} ===\n{doc_text[:max_chars]}"
            except Exception as e:
                print(f"Error processing {filename}: {str(e)}")
        
        if not documents:
            return None
        
        # Return multi-document context
        if len(documents) == 1:
            return documents[0]
        else:
            return {
                "filename": f"{len(documents)} documents",
                "path": upload_dir,
                "text": combined_text,
                "type": "multi-document",
                "pages": sum(d.get("pages", 0) for d in documents),
                "documents": documents,
                "is_multi": True
            }
    
    async def _detect_unknowns(self, text: str) -> List[str]:
        """Detect concepts not in semantic memory"""
        concepts = self.cognitive_core.question_engine._extract_concepts(text)
        unknowns = []
        
        for concept in concepts:
            existing = await self.cognitive_core.semantic_memory.recall_concept(concept)
            if not existing:
                unknowns.append(concept)
        
        return unknowns[:5]  # Limit to top 5
    
    def _generate_internal_questions(self, user_input: str, unknowns: List[str]) -> List[str]:
        """
        Generate internal questions (not shown to user)
        These guide research and understanding
        """
        questions = []
        
        # Questions about unknowns
        for unknown in unknowns[:3]:
            questions.extend([
                f"What is {unknown}?",
                f"How does {unknown} relate to the user's question?",
                f"What should I know about {unknown}?"
            ])
        
        # Meta-questions about the request
        questions.extend([
            f"What is the user really asking about in '{user_input}'?",
            f"What context am I missing?",
            f"What would a complete answer include?"
        ])
        
        return questions
    
    async def _self_research(self, unknowns: List[str], questions: List[str], document_context: Optional[Dict] = None) -> List[Dict]:
        """
        Self-research on unknowns using available resources
        INCLUDING uploaded documents
        """
        research_results = []
        
        # 0. Document context (highest priority)
        if document_context:
            research_results.append({
                "source": "uploaded_document",
                "filename": document_context["filename"],
                "text": document_context["text"][:2000],  # First 2000 chars
                "data": document_context
            })
        
        # 1. Dictionary lookup for unknowns
        for unknown in unknowns[:3]:
            try:
                result = await self.dictionary.lookup_and_store(unknown)
                if result["status"] == "added":
                    research_results.append({
                        "source": "dictionary",
                        "concept": unknown,
                        "data": result["data"]
                    })
            except Exception:
                pass
        
        # 2. Memory recall
        for unknown in unknowns:
            try:
                concept = await self.cognitive_core.semantic_memory.recall_concept(unknown)
                if concept:
                    research_results.append({
                        "source": "memory",
                        "concept": unknown,
                        "data": concept
                    })
            except Exception:
                pass
        
        # 3. Web research (if enabled and needed)
        # TODO: Add web search integration when available
        
        return research_results
    
    async def _synthesize_understanding(self, user_input: str, research_results: List[Dict], document_context: Optional[Dict] = None) -> Dict:
        """
        Synthesize understanding from research
        """
        # Calculate confidence based on research
        confidence = min(len(research_results) * 20, 100)
        
        # Boost confidence if we have document context
        if document_context:
            confidence = min(confidence + 30, 100)
        
        # Extract key information
        key_facts = []
        document_content = None
        
        for result in research_results:
            if result["source"] == "uploaded_document":
                document_content = result["text"]
                key_facts.insert(0, f"From {result['filename']}: {document_content[:300]}")
            elif result["source"] == "dictionary":
                key_facts.append(result["data"]["primary_definition"])
            elif result["source"] == "memory":
                key_facts.append(result["data"]["definition"])
        
        return {
            "confidence": confidence,
            "key_facts": key_facts[:5],
            "sources_used": len(research_results),
            "understanding_formed": len(key_facts) > 0,
            "has_document": document_content is not None,
            "document_content": document_content
        }
    
    async def _generate_confident_response(
        self, 
        user_input: str, 
        synthesized: Dict,
        research_results: List[Dict],
        document_context: Optional[Dict] = None,
        confusion_concepts: List[str] = None,
        explain_mode: bool = False,
        structured_response: str = None  # Frontend-generated structured response
    ) -> (str, Optional[Dict]):
        """
        Generate natural, conversational response using QUANTUM BRAIN
        
        UPGRADED FLOW:
        1. Quantum Brain generates raw chaotic response
        2. If structured_response provided, Markov weaves both
        3. Chaos engine adds personality on top
        
        If explain_mode=True, also returns explanation trace from QuantumBrain.
        
        PRIORITIZE document content when available
        """
        # Get document content if available
        doc_content = None
        doc_filename = None
        
        if synthesized.get("has_document") and document_context:
            doc_content = synthesized.get("document_content") or document_context.get("text", "")
            doc_filename = document_context.get("filename", "uploaded document")
        
        # UNIFIED: Use Unified Quantum Brain with chaos preservation
        try:
            from unified_quantum_brain import get_unified_brain
            from quantum_brain import get_quantum_brain
            from quantum_language_engine import QuantumLanguageEngine
            from chaos_engine import get_chaos_engine
            from quote_engine import get_quote_engine
            from personality_engine import get_personality_engine
            from dream_state import get_dream_engine

            brain = await get_quantum_brain(self.cognitive_core.db)

            # Create language engine and hybrid generator for raw fragments / fallback
            lang_engine = QuantumLanguageEngine()
            hybrid = create_hybrid_generator(lang_engine)

            quotes = get_quote_engine()
            personality = get_personality_engine()
            dreams = get_dream_engine(self.cognitive_core.db)
            chaos = get_chaos_engine(quotes, personality, dreams)
            chaos.set_chaos_level(1.0)  # MAX chaos for raw artifacts

            unified = await get_unified_brain(brain, hybrid, chaos)

            # Force raw chaotic output: always use hybrid (Markov) path
            # Route factual/math to quantum brain, philosophical to hybrid
            import re
            is_math = bool(re.search(r'[\d]+\s*[\+\-\*\/\=]\s*[\d]+', user_input))
            is_factual = any(w in user_input.lower() for w in [
                'how many', 'how much', 'when did', 'where is',
                'what year', 'convert', 'distance', 'population',
                'calculate', 'solve', 'equals', 'what is the value'
            ])
            chaotic_understanding = 0.9 if (is_math or is_factual) else 0.1

            result = await unified.think_preserving_chaos(
                user_input=user_input,
                context={
                    "memories": [],
                    "document": doc_content,
                    "document_filename": doc_filename,
                    "conversation_history": getattr(self, 'conversation_history', None),
                    "research": research_results,
                    "confidence": synthesized.get("confidence", 50)
                },
                confusion_concepts=confusion_concepts or [],
                raw_backend_fragments=[],
                base_understanding_score=chaotic_understanding
            )

            raw_chaotic = result["response"]

            # DEBUG
            import sys
            print(f"[DEBUG] structured_response length: {len(structured_response) if structured_response else 0}", file=sys.stderr)
            print(f"[DEBUG] raw_chaotic length: {len(raw_chaotic)}", file=sys.stderr)

            # If structured response provided from frontend, weave with adaptive Markov source-switching
            if structured_response:
                import re
                # Split into sentences (simple punctuation split)
                chaotic_sentences = [s.strip() for s in re.split(r'[.!?]+', raw_chaotic) if s.strip()]
                structured_sentences = [s.strip() for s in re.split(r'[.!?]+', structured_response) if s.strip()]
                
                # Ensure punctuation
                chaotic_sentences = [s + '.' if not s.endswith(('.', '!', '?')) else s for s in chaotic_sentences]
                structured_sentences = [s + '.' if not s.endswith(('.', '!', '?')) else s for s in structured_sentences]
                
                # Shuffle structured to avoid rigid pairing; keep chaotic order (Markov)
                import random as _random
                _random.shuffle(structured_sentences)
                
                # Adaptive Markov: base switch probability, adjust based on remaining counts
                base_p_switch = 0.6
                woven = []
                idx_s = 0
                idx_c = 0
                # Start with either structured or chaotic randomly
                current = 'structured' if _random.random() < 0.5 else 'chaotic'
                
                while idx_s < len(structured_sentences) or idx_c < len(chaotic_sentences):
                    # Compute remaining
                    rem_s = len(structured_sentences) - idx_s
                    rem_c = len(chaotic_sentences) - idx_c
                    total_rem = rem_s + rem_c
                    
                    # Adaptive bias: if one pool is much larger, increase chance to use the smaller one
                    if total_rem > 0:
                        ratio_s = rem_s / total_rem
                        ratio_c = rem_c / total_rem
                        # If one is less than 40% of remaining, bias towards it
                        if ratio_s < 0.4:
                            # Bias to switch to structured if currently chaotic, and stay if structured
                            p_switch = base_p_switch * 1.5 if current == 'chaotic' else base_p_switch * 0.5
                        elif ratio_c < 0.4:
                            p_switch = base_p_switch * 1.5 if current == 'structured' else base_p_switch * 0.5
                        else:
                            p_switch = base_p_switch
                    else:
                        p_switch = base_p_switch
                    
                    # Clamp probability
                    p_switch = max(0.1, min(0.9, p_switch))
                    
                    if current == 'structured' and idx_s < len(structured_sentences):
                        woven.append(structured_sentences[idx_s])
                        idx_s += 1
                        # Decide next source
                        current = 'chaotic' if _random.random() < p_switch else 'structured'
                    elif current == 'chaotic' and idx_c < len(chaotic_sentences):
                        woven.append(chaotic_sentences[idx_c])
                        idx_c += 1
                        current = 'structured' if _random.random() < p_switch else 'chaotic'
                    else:
                        # Current pool exhausted, switch to other
                        current = 'structured' if idx_s < len(structured_sentences) else 'chaotic'
                
                response = ' '.join(woven)
            else:
                response = raw_chaotic

            if explain_mode:
                explanation = {
                    "reasoning_path": ["UnifiedQuantumBrain preservation pipeline"],
                    "confidence_score": chaotic_understanding,
                    "engines_used": ["QuantumBrain", "HybridGenerator", "ChaosEngine"],
                    "steps": [
                        {"step": "Unified generation with chaos preservation", "engine": "UnifiedQuantumBrain", "confidence_contribution": 1.0}
                    ],
                    "summary": "Response generated with personality stacking and raw fragment preservation.",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                }
                # Add entelechy cascade from semantic context
                try:
                    semantic_context = brain.collapse_engine.get_semantic_context(user_input)
                    entelechy = brain._compute_entelechy_cascade(response, semantic_context)
                    explanation["entelechy"] = entelechy
                except Exception as e:
                    logger.warning(f"Failed to compute entelechy cascade: {e}")
            else:
                explanation = None

            print(f"[UNIFIED BRAIN] Response generated (chaos={chaos.chaos_level:.2f}, preserved_weirdness={result['preserved_weirdness']})")

            return response, explanation
            
        except ImportError as e:
            import traceback
            print(f"Unified Brain import error: {str(e)}\n{traceback.format_exc()}")
            # Fallback to basic response
            return self._fallback_response(user_input, synthesized, document_context), None
        except Exception as e:
            import traceback
            print(f"Quantum Brain error: {str(e)}\n{traceback.format_exc()}")
            # Fallback to basic response
            return self._fallback_response(user_input, synthesized, document_context), None
    
    async def _legacy_llm_response(
        self,
        user_input: str,
        synthesized: Dict,
        research_results: List[Dict],
        document_context: Optional[Dict] = None
    ) -> str:
        """Legacy LLM response method (fallback only)"""
        doc_content = None
        
        if synthesized.get("has_document") and document_context:
            doc_content = synthesized.get("document_content") or document_context.get("text", "")
        
        try:
            raise NotImplementedError('LLM removed')
            
            context = {
                "concepts": [],
                "understanding_score": synthesized.get("confidence", 50) / 100,
                "related_concepts": []
            }
            
            for result in research_results:
                if result["source"] == "dictionary":
                    context["concepts"].append(result.get("concept", ""))
                elif result["source"] == "memory":
                    context["related_concepts"].append(result.get("concept", ""))
            
            response = await llm.llm.generate_response(
                user_input=user_input,
                context=context,
                document_content=doc_content,
                conversation_history=getattr(self, 'conversation_history', None)
            )
            
            return response
            
        except Exception as e:
            print(f"Legacy LLM error: {str(e)}")
            return self._fallback_response(user_input, synthesized, document_context)
    
    def _fallback_response(
        self, 
        user_input: str, 
        synthesized: Dict,
        document_context: Optional[Dict] = None
    ) -> (str, Optional[Dict]):
        """Fallback response when LLM/QuantumBrain unavailable. Returns (response, None)."""
        # If asking about a document, respond with document content
        if synthesized.get("has_document") and document_context:
            doc_text = synthesized.get("document_content", "")
            filename = document_context.get("filename", "the document")
            
            # Extract meaningful content (first few sentences or paragraphs)
            preview = doc_text[:500].strip() if doc_text else "Unable to extract content."
            
            response = preview
            
            if doc_text and len(doc_text) > 500:
                response += "...\n\nWhat specific aspect would you like to explore?"
            
            return response, None
        
        # Otherwise, normal response flow
        confidence = synthesized.get("confidence", 0)
        
        if confidence >= 60 and synthesized.get("understanding_formed"):
            facts = synthesized.get("key_facts", [])
            
            if facts:
                main_point = facts[0]
                response = f"{main_point}"
                
                if len(facts) > 1:
                    response += f" {facts[1]}"
                
                response += " What would you like to know more about?"
                
                return response, None
            
        elif confidence >= 30:
            if synthesized.get("key_facts"):
                return f"From what I understand: {synthesized['key_facts'][0]}. I'm still learning about this. What's your take on it?", None
            else:
                return "I'm exploring this concept now. What brings this up for you?", None
        
        return "I haven't encountered this before. Tell me more about it - I'm interested to learn.", None
    
    async def _store_thinking_process(self, user_input: str, questions: List[str], research: List[Dict]):
        """
        Store the thinking process for growth tracking
        (This is where the AI actually learns)
        """
        # Store questions in philosophical memory
        for question in questions[:3]:
            await self.cognitive_core.philosophical_memory.store_question(
                question=question,
                context=user_input,
                depth=2  # Deeper than surface questions
            )
        
        # Store insight about the process
        if len(research) > 0:
            insight = f"Learned about {len(research)} concepts through self-research"
            await self.cognitive_core.philosophical_memory.store_insight(
                insight=insight,
                wisdom_level=2
            )
        
        # Record growth event
        await self.cognitive_core.growth_tracker.record_growth_event(
            event_type="thinking_mode_research",
            details={
                "questions_generated": len(questions),
                "research_conducted": len(research),
                "thinking_mode": "hidden"
            }
        )
    
    def toggle_thinking_display(self, show: bool):
        """User control: show/hide thinking process"""
        self.show_thinking = show
        return f"Thinking mode display: {'ON' if show else 'OFF'}"





# Singleton
_hidden_thinking = None


def get_hidden_thinking(cognitive_core, dictionary, universal_explorer):
    """Get or create hidden thinking mode."""
    global _hidden_thinking
    if _hidden_thinking is None:
        _hidden_thinking = HiddenThinkingMode(cognitive_core, dictionary, universal_explorer)
    return _hidden_thinking
