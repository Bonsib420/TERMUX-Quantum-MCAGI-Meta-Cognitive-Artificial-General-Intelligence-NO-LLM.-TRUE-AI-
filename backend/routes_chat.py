"""
🔮 Chat Routes
===============
Chat endpoints, session management, and command processing.
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional, Any
import uuid
import os
import logging
import time
from datetime import datetime, timezone

import shared_state as state
from thinking_commands import ThinkingModeCommands
from chat_helpers import (
    get_memory_summary, do_deep_research, process_shared_link,
    list_all_documents, generate_speech, get_help_text,
    analyze_book_characters, analyze_book_timeline,
    analyze_book_worldbuilding, analyze_book_feedback
)
from chat_models import get_chat_store

logger = logging.getLogger("quantum_ai")
router = APIRouter(prefix="/api")


def _build_command_explanation(command: str, result: str) -> Dict:
    """Build explanation for a slash command execution."""
    return {
        "reasoning_path": [f"Detected command: {command}", "Parse arguments", "Execute", "Return result"],
        "confidence_score": 1.0,
        "engines_used": ["CommandInterface"],
        "steps": [
            {"step": "Command detection", "engine": "CommandInterface", "confidence_contribution": 0.3},
            {"step": f"Execute {command}", "engine": "CommandInterface", "confidence_contribution": 0.7}
        ],
        "summary": f"Command {command} executed successfully.",
        "timestamp": datetime.now(timezone.utc).isoformat()
    }


async def _handle_command(content: str, explain_mode: bool = False) -> Optional["ChatResponse"]:
    """
    Handle slash commands. Returns ChatResponse if content is a command, else None.
    """
    content = content.strip()
    if not content.startswith('/'):
        return None
    
    parts = content.split()
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []
    session_id = str(uuid.uuid4())[:8]  # dummy for response; real session_id comes from message
    
    response_text = ""
    explanation = None
    
    try:
        if cmd == '/explain' and args:
            # Force explain mode for the given query
            # Treat the rest as a normal chat with explain_mode=True
            # We'll short-circuit: call hidden_thinking directly with query
            combined = ' '.join(args)
            # Need context and history? None for simplicity.
            result = await state.hidden_thinking.process_with_thinking(
                combined,
                context=None,
                conversation_history=[],
                explain_mode=True
            )
            response_text = result["response"]
            explanation = result.get("explanation")
            # Also append note that command was used
            response_text = f"[Command: /explain]\n{response_text}"
            if explain_mode:
                # Already explained
                pass
        elif cmd == '/explain' and not args:
            response_text = "Usage: /explain <your question>"
        elif cmd == '/status':
            import platform
            uptime_seconds = time.time() - getattr(state, 'start_time', time.time())
            status_lines = [
                "Quantum AI System Status:",
                f"  Cognitive Core: {'✅' if state.cognitive_core else '❌'}",
                f"  Universal Explorer: {'✅' if state.universal_explorer else '❌'}",
                f"  Hidden Thinking: {'✅' if state.hidden_thinking else '❌'}",
                f"  Uptime: {int(uptime_seconds)}s",
                f"  Platform: {platform.system()} {platform.release()}",
            ]
            response_text = "\n".join(status_lines)
        elif cmd == '/save':
            # The system auto-saves on every message; just acknowledge.
            response_text = "State automatically saved to local storage."
        elif cmd in ('/cloud-save', '/cloud-status', '/cloud-load'):
            try:
                from wolfram_cloud import cloud_save, cloud_status, cloud_load
                # But these functions expect LocalMemory object; server uses different storage.
                response_text = f"Wolfram Cloud command '{cmd}' is only available in local chat mode (chat.py)."
            except ImportError:
                response_text = "Wolfram Cloud not available."
        elif cmd == '/knowledge' and args:
            topic = ' '.join(args)
            try:
                from knowledge_base import get_knowledge_base
                kb = get_knowledge_base()
                explanation_text = kb.get_topic_explanation(topic)
                if explanation_text:
                    response_text = explanation_text
                else:
                    response_text = f"No knowledge available on: {topic}"
            except Exception as e:
                response_text = f"Knowledge lookup error: {e}"
        elif cmd == '/analyze' and args:
            text = ' '.join(args)
            try:
                from text_analyzer import get_text_analyzer
                analyzer = get_text_analyzer()
                analysis = analyzer.analyze(text)
                lines = [
                    "Text Analysis:",
                    f"  Sentiment: {analysis.get('sentiment', 'unknown')}",
                    f"  Complexity: {analysis.get('complexity', 'unknown')}",
                    f"  Topics: {', '.join(analysis.get('topics', []))}",
                    f"  Word count: {analysis.get('word_count', 0)}"
                ]
                response_text = "\n".join(lines)
            except Exception as e:
                response_text = f"Analysis error: {e}"
        elif cmd == '/personality':
            try:
                from personality_engine import get_personality_engine
                personality = get_personality_engine()
                response_text = personality.get_personality_summary()
            except Exception as e:
                response_text = f"Personality error: {e}"
        elif cmd == '/research':
            if not args:
                response_text = "Usage: /research <topic> -<depth>\nExample: /research Evolution of Religion -30"
            else:
                depth = 10
                topic_parts = []
                for a in args:
                    if a.startswith('-') and a[1:].isdigit():
                        depth = int(a[1:])
                    else:
                        topic_parts.append(a)
                topic = ' '.join(topic_parts)
                try:
                    research_prompt = f"Provide {depth} detailed, numbered research points about: {topic}. Each point should be substantive and informative."
                    result = await state.hidden_thinking.process_with_thinking(
                        research_prompt,
                        context={"mode": "research", "depth": depth, "topic": topic},
                        conversation_history=[],
                        explain_mode=explain_mode
                    )
                    response_text = f"🔬 Research: {topic}\n\n" + result["response"]
                    if explain_mode:
                        explanation = result.get("explanation")
                except Exception as e:
                    response_text = f"Research error: {e}"
        else:
            response_text = f"Unknown command: {cmd}. Supported: /explain, /status, /save, /cloud-save, /cloud-status, /cloud-load, /knowledge <topic>, /analyze <text>, /personality, /research <topic> -<depth>"
        
        if explain_mode:
            explanation = _build_command_explanation(cmd, response_text)
        
        return ChatResponse(
            questions=[],
            response=resp,
            understanding={"command": cmd},
            concepts=[],
            session_id=session_id,
            explanation=explanation
        )
    except Exception as e:
        logger.error(f"Command error ({cmd}): {e}")
        return ChatResponse(
            questions=[],
            response=f"Error executing command: {e}",
            understanding={"command": cmd, "error": True},
            concepts=[],
            session_id=str(uuid.uuid4())[:8],
            explanation=None
        )


class ChatMessage(BaseModel):
    """ChatMessage - Auto-documented by self-evolution."""
    content: str
    mode: Optional[str] = None  # 'quantum' or 'algorithmic'
    context: Optional[Dict] = None
    session_id: Optional[str] = None
    files: Optional[List[Dict[str, Any]]] = None  # List of {filename, size}
    explain_mode: Optional[bool] = False  # If True, return detailed reasoning trace
    structured_response: Optional[str] = None  # Frontend-generated structured response for Markov weaving

class ChatResponse(BaseModel):
    """ChatResponse - Auto-documented by self-evolution."""
    questions: List[str]
    response: str
    understanding: Dict
    concepts: List[str]
    session_id: Optional[str] = None
    explanation: Optional[Dict] = None  # Explanation trace when explain_mode=True


@router.post("/quantum/chat", response_model=ChatResponse)
async def quantum_chat(message: ChatMessage):
    """
    ARTICLE 1.1 - Prime Directive of Questioning (HIDDEN MODE)
    
    Process user input with hidden thinking mode.
    AI thinks, questions, researches internally - user sees clean conversation.
    Supports conversation history via session_id.
    """
    try:
        # Generate or use provided session ID
        session_id = message.session_id or str(uuid.uuid4())
        
        # Reset activity timer (user is interacting)
        state.last_activity_time = datetime.now(timezone.utc)
        
        # Wake from dream if dreaming
        try:
            from dream_state import get_dream_engine
            dream_engine = get_dream_engine(state.db)
            await dream_engine.mark_active()
        except:
            pass
        
        # Check for thinking mode commands
        command = ThinkingModeCommands.parse_command(message.content)
        
        if command:
            if command["command"] == "thinking_on":
                state.hidden_thinking.toggle_thinking_display(True)
                return ChatResponse(
                    questions=[],
                    response="🧠 Thinking mode display: ON. You'll now see my internal process.",
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            elif command["command"] == "thinking_off":
                state.hidden_thinking.toggle_thinking_display(False)
                return ChatResponse(
                    questions=[],
                    response="🧠 Thinking mode display: OFF. Clean conversation mode.",
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            elif command["command"] == "thinking_status":
                status = "ON (visible)" if state.hidden_thinking.show_thinking else "OFF (hidden)"
                return ChatResponse(
                    questions=[],
                    response=f"🧠 Current thinking mode: {status}",
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            elif command["command"] == "read_file":
                # Process uploaded file
                filename = command["filename"] or "last uploaded file"
                
                # Get list of uploaded files
                import os
                upload_dir = "/app/uploads"
                if os.path.exists(upload_dir):
                    files = [f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))]
                    
                    if files:
                        # Use specified file or most recent
                        if command["filename"]:
                            target_file = command["filename"]
                        else:
                            target_file = files[-1]  # Most recent
                        
                        file_path = os.path.join(upload_dir, target_file)
                        
                        # Process the document
                        result = await state.universal_explorer.documents.process_document(file_path)
                        
                        if "error" not in result:
                            # Extract and summarize
                            text = result.get("text", "")[:500]
                            response = f"📄 Read {target_file}:\n\nI've processed this document. {text[:200]}...\n\nWhat would you like to know about it?"
                        else:
                            response = f"❌ Couldn't read {target_file}: {result['error']}"
                    else:
                        response = "No files uploaded yet. Use the Explorer tab to upload files."
                else:
                    response = "Upload directory not found."
                
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "memory":
                # Show what AI has learned
                response = await get_memory_summary(session_id)
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "research":
                # Deep research on a topic
                topic = command.get("topic", "")
                if not topic:
                    return ChatResponse(
                        questions=[],
                        response="🔍 Usage: `!research <topic>`\n\nExample: `!research quantum entanglement`",
                        understanding={},
                        concepts=[],
                        session_id=session_id
                    )
                
                response = await do_deep_research(topic)
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "link":
                # Download file from URL
                url = command.get("url", "")
                if not url:
                    return ChatResponse(
                        questions=[],
                        response="🔗 Usage: `!link <url>`\n\nSupported:\n• Google Drive links\n• Dropbox links\n• OneDrive links\n• Direct file URLs\n\nExample: `!link https://drive.google.com/file/d/...`",
                        understanding={},
                        concepts=[],
                        session_id=session_id
                    )
                
                response = await process_shared_link(url)
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "docs":
                # List all documents
                response = await list_all_documents()
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "speak":
                # Text to speech
                text = command.get("text", "")
                if not text:
                    return ChatResponse(
                        questions=[],
                        response="🔊 Usage: `!speak <text>`\n\nExample: `!speak Hello, I am Quantum AI`\n\nOr just chat normally and use the speaker button on my responses!",
                        understanding={},
                        concepts=[],
                        session_id=session_id
                    )
                
                # Generate TTS
                audio_url = await generate_speech(text)
                response = f"🔊 **Speech Generated**\n\n\"{text[:100]}{'...' if len(text) > 100 else ''}\"\n\n[Audio URL: {audio_url}]" if audio_url else f"🔊 Text to speak:\n\n\"{text}\"\n\n_Use your browser's text-to-speech or copy this text._"
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "imagine":
                # Generate image
                prompt = command.get("prompt", "")
                if not prompt:
                    return ChatResponse(
                        questions=[],
                        response="🎨 Usage: `!imagine <description>`\n\nExample: `!imagine a cosmic landscape with nebulas and stars`",
                        understanding={},
                        concepts=[],
                        session_id=session_id
                    )
                
                try:
                    import base64
                    
                    image_gen = OpenAIImageGeneration(api_key=api_key)
                    images = await image_gen.generate_images(prompt=prompt, model="gpt-image-1.5", number_of_images=1)
                    
                    if images and len(images) > 0:
                        image_base64 = base64.b64encode(images[0]).decode('utf-8')
                        filename = f"generated_{uuid.uuid4().hex[:8]}.png"
                        with open(f"/app/uploads/{filename}", "wb") as f:
                            f.write(images[0])
                        
                        response = f"🎨 **Image Generated**\n\nPrompt: \"{prompt}\"\n\nSaved as: {filename}\n\n![Generated Image](data:image/png;base64,{image_base64[:50]}...)"
                    else:
                        response = "🎨 Image generation failed. Please try again."
                except Exception as e:
                    response = f"🎨 Image generation error: {str(e)}"
                
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "export":
                # Export chat or memory
                target = command.get("target", "chat")
                if target == "memory":
                    response = "📤 **Export Memory**\n\nUse the API endpoint: `GET /api/memory/export`\n\nOr click the Export button in the Memory screen."
                else:
                    response = f"📤 **Export Conversation**\n\nUse the API: `GET /api/chat/export/{session_id}`\n\nOr click the Export button in Chat."
                
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "graph":
                # Knowledge graph info
                response = "🕸️ **Knowledge Graph**\n\nView your knowledge graph visualization in the **Memory** screen.\n\nThe graph shows:\n• Concepts you've learned (nodes)\n• Relationships between concepts (edges)\n• Insights (special nodes)\n\nAPI: `GET /api/knowledge/graph`"
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "characters":
                # Extract characters from document
                response = await analyze_book_characters()
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "timeline":
                # Generate timeline
                response = await analyze_book_timeline()
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "worldbuilding":
                # Extract world details
                response = await analyze_book_worldbuilding()
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "feedback":
                # Writing feedback
                response = await analyze_book_feedback()
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "help":
                # Show all commands
                response = get_help_text()
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={},
                    concepts=[],
                    session_id=session_id
                )
            
            # --- Slash commands (compatible with chat.py) ---
            elif command["command"] == "cloud_save":
                try:
                    from wolfram_cloud import cloud_save
                    # cloud_save expects LocalMemory, not available here
                    response = "Wolfram Cloud save is only available in local chat mode (run `python chat.py`)."
                except ImportError:
                    response = "Wolfram Cloud not available."
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={"command": "cloud_save"},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "cloud_status":
                try:
                    from wolfram_cloud import cloud_status
                    status = cloud_status()
                    response = f"Wolfram Cloud status: {status}"
                except ImportError:
                    response = "Wolfram Cloud not available."
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={"command": "cloud_status"},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "cloud_load":
                try:
                    from wolfram_cloud import cloud_load
                    data = cloud_load()
                    response = f"Cloud data loaded: {data}" if data else "No data in cloud."
                except ImportError:
                    response = "Wolfram Cloud not available."
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={"command": "cloud_load"},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "status":
                import platform
                uptime_seconds = getattr(state, 'start_time', None)
                if uptime_seconds is None:
                    uptime = "unknown"
                else:
                    uptime = f"{int(time.time() - state.start_time)}s"
                lines = [
                    "Quantum AI System Status:",
                    f"  Cognitive Core: {'✅' if state.cognitive_core else '❌'}",
                    f"  Universal Explorer: {'✅' if state.universal_explorer else '❌'}",
                    f"  Hidden Thinking: {'✅' if state.hidden_thinking else '❌'}",
                    f"  Uptime: {uptime}",
                    f"  Platform: {platform.system()} {platform.release()}",
                ]
                response = "\n".join(lines)
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={"command": "status"},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "save":
                response = "State automatically saved to local storage after each message."
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={"command": "save"},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "explain_help":
                response = "Use /explain <your question> to get a detailed reasoning trace with PennyLane quantum processing.\n\nExample: `/explain What is quantum superposition?`"
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={"command": "explain_help"},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "explain_query":
                query = command.get("query", "")
                if not query:
                    response = "Usage: /explain <your question>"
                    return ChatResponse(questions=[], response=response, understanding={"command": "explain_help"}, concepts=[], session_id=session_id)
                # Process with hidden_thinking in explain mode
                result = await state.hidden_thinking.process_with_thinking(
                    query,
                    context=None,
                    conversation_history=[],
                    explain_mode=True
                )
                response = result["response"]
                explanation = result.get("explanation")
                return ChatResponse(
                    questions=result.get("internal_questions", []),
                    response=response,
                    understanding={"confidence": result["confidence"], "research_done": result["research_done"]},
                    concepts=result.get("concepts", []),
                    session_id=session_id,
                    explanation=explanation
                )
            
            elif command["command"] == "knowledge":
                topic = command.get("topic", "")
                if not topic:
                    response = "Usage: /knowledge <topic>"
                else:
                    try:
                        from knowledge_base import get_knowledge_base
                        kb = get_knowledge_base()
                        explanation = kb.get_topic_explanation(topic)
                        response = explanation if explanation else f"No knowledge available on: {topic}"
                    except Exception as e:
                        response = f"Knowledge lookup error: {e}"
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={"command": "knowledge", "topic": topic},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "analyze":
                text = command.get("text", "")
                if not text:
                    response = "Usage: /analyze <text>"
                else:
                    try:
                        from text_analyzer import get_text_analyzer
                        analyzer = get_text_analyzer()
                        analysis = analyzer.analyze(text)
                        lines = [
                            "Text Analysis:",
                            f"  Sentiment: {analysis.get('sentiment', 'unknown')}",
                            f"  Complexity: {analysis.get('complexity', 'unknown')}",
                            f"  Topics: {', '.join(analysis.get('topics', []))}",
                            f"  Word count: {analysis.get('word_count', 0)}"
                        ]
                        response = "\n".join(lines)
                    except Exception as e:
                        response = f"Analysis error: {e}"
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={"command": "analyze"},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "personality":
                try:
                    from personality_engine import get_personality_engine
                    personality = get_personality_engine()
                    response = personality.get_personality_summary()
                except Exception as e:
                    response = f"Personality error: {e}"
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={"command": "personality"},
                    concepts=[],
                    session_id=session_id
                )
            
            elif command["command"] == "collapse":
                text = command.get("text", "")
                if not text:
                    response = "Usage: /collapse <text>"
                else:
                    try:
                        # Use QuantumBrain's collapse engine
                        from quantum_brain import get_quantum_brain
                        brain = await get_quantum_brain(state.db)
                        ctx = brain.collapse_engine.get_semantic_context(text)
                        lines = [
                            "Semantic Collapse Analysis:",
                            f"  Keywords: {ctx['keywords']}",
                            f"  Collapse strength: {ctx['collapse_strength']:.2f}",
                        ]
                        for kw, paths in ctx['semantic_paths'].items():
                            lines.append(f"  {kw} -> {paths}")
                        response = "\n".join(lines)
                    except Exception as e:
                        response = f"Collapse error: {e}"
                return ChatResponse(
                    questions=[],
                    response=response,
                    understanding={"command": "collapse"},
                    concepts=[],
                    session_id=session_id
                )
            
            # End of slash commands
        
        # Get or create conversation in ChatStore
        store = get_chat_store()
        conv = store.get_conversation(session_id)
        if not conv:
            # Create new conversation with first user message as title
            title = message.content[:50] + ("..." if len(message.content) > 50 else "")
            conv = store.create_conversation(user_id="default", title=title)
            # The create_conversation returns new conv with id, but we need to set the id to session_id? 
            # ChatStore creates its own ID. We need to ensure it matches session_id.
            # Workaround: we'll just add messages to a new conv and then later we need to map session_id to conv.id
            # Note: ChatStore uses local file storage; session_id handling may be simplified.
            pass

        # Get conversation history for context from local file storage
        history = await get_conversation_history(session_id, limit=10)
        
        # DEBUG: log structured_response
        logger.info(f"DEBUG: structured_response from message: {message.structured_response[:50] if message.structured_response else 'None'}")
        
        # Process with hidden thinking mode
        result = await state.hidden_thinking.process_with_thinking(
            message.content,
            message.context,
            conversation_history=history,
            explain_mode=message.explain_mode,
            structured_response=message.structured_response
        )
        
        # Store this exchange in history (local file storage)
        await store_chat_message(session_id, "user", message.content)
        await store_chat_message(session_id, "assistant", result["response"])
        
        # Format response with thinking log if enabled (legacy thinking display)
        response_text = result["response"]
        if result.get("thinking_log") and state.hidden_thinking.show_thinking:
            thinking_display = "\n\n--- THINKING PROCESS ---\n" + "\n".join(result["thinking_log"])
            response_text = response_text + thinking_display
        
        resp = result["response"]
        if isinstance(resp, tuple): resp = resp[0]
        return ChatResponse(
            questions=[str(q) for q in result.get("internal_questions", [])] if state.hidden_thinking.show_thinking else [],
            response=resp,
            understanding={"confidence": result["confidence"], "research_done": result["research_done"]},
            concepts=result.get("concepts", []),
            session_id=session_id,
            explanation=result.get("explanation") if message.explain_mode else None
        )
        
    except Exception as e:
        import traceback
        logger.error(f"Chat error: {str(e)}\n{traceback.format_exc()}")
        # Fallback to basic mode
        result = await state.cognitive_core.process_input(
            message.content, 
            message.context,
        )
        return ChatResponse(
            questions=result["questions"],
            response=result["response"],
            understanding=result["understanding"],
            concepts=result["concepts"],
            session_id=message.session_id
        )


# ============================================================================
# CONVERSATION HISTORY HELPERS
# ============================================================================

async def store_chat_message(session_id: str, role: str, content: str):
    """Store a chat message in local file storage"""
    doc = {
        "session_id": session_id,
        "role": role,
        "content": content,
        "timestamp": datetime.now(timezone.utc).isoformat()
    }
    await state.db.chat_history.insert_one(doc)


async def get_conversation_history(session_id: str, limit: int = 10) -> List[Dict]:
    """Get recent conversation history for a session from local storage"""
    cursor = state.db.chat_history.find(
        {"session_id": session_id},
        {"_id": 0, "role": 1, "content": 1, "timestamp": 1}
    ).sort("timestamp", -1).limit(limit)
    
    messages = await cursor.to_list(length=limit)
    # Return in chronological order
    return list(reversed(messages))


@router.get("/chat/history/{session_id}")
async def get_chat_history(session_id: str, limit: int = 50):
    """Get conversation history for a session"""
    try:
        history = await get_conversation_history(session_id, limit)
        return {"session_id": session_id, "messages": history, "count": len(history)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/chat/history/{session_id}")
async def clear_chat_history(session_id: str):
    """Clear conversation history for a session"""
    try:
        result = await state.db.chat_history.delete_many({"session_id": session_id})
        return {"session_id": session_id, "deleted": result.deleted_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/chat/sessions")
async def list_chat_sessions():
    """List all chat sessions"""
    try:
        # Fetch all messages (with limit for performance)
        cursor = state.db.chat_history.find(
            {}, 
            {"_id": 0, "session_id": 1, "timestamp": 1}
        ).sort("timestamp", -1).limit(1000)
        messages = await cursor.to_list(length=1000)

        # Group by session_id
        sessions_dict = {}
        for msg in messages:
            sid = msg.get("session_id")
            if not sid:
                continue
            if sid not in sessions_dict:
                sessions_dict[sid] = {"session_id": sid, "message_count": 0, "last_message": None}
            sessions_dict[sid]["message_count"] += 1
            ts = msg.get("timestamp")
            if ts:
                if sessions_dict[sid]["last_message"] is None or ts > sessions_dict[sid]["last_message"]:
                    sessions_dict[sid]["last_message"] = ts

        sessions = list(sessions_dict.values())
        # Sort by last_message descending (handle None)
        sessions.sort(key=lambda x: x["last_message"] or "", reverse=True)
        sessions = sessions[:20]

        return {"sessions": sessions}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ============================================================================
# COMMAND HELPERS (!memory, !research)
# ============================================================================

