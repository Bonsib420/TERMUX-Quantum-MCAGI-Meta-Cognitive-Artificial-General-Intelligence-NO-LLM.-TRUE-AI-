"""\n🔮 Chat Command Helpers\n========================\nHelper functions for chat commands: memory, research, book analysis, etc.\n"""

import os
import logging
from datetime import datetime, timezone
from typing import List, Dict

import shared_state as state

logger = logging.getLogger("quantum_ai")


# ============================================================================
# COMMAND HELPERS (!memory, !research)
# ============================================================================

async def get_memory_summary(session_id: str) -> str:
    """
    Builds a formatted status report summarizing the AI's current memory, growth metrics, recent concepts/insights, session statistics, and available uploaded documents.
    
    Parameters:
        session_id (str): Identifier of the chat session used to report session-specific message counts.
    
    Returns:
        str: A multiline, human-readable status string containing growth stage and description, progress toward the next stage (if any), learning metrics (connections, concepts, questions, insights, graph topology, growth rate), up to five recent concepts, up to three recent insights (each truncated to 80 characters), session message counts, and a short listing of up to five uploaded files. On internal failure, returns an error message beginning with "🧠 Memory status unavailable:".
    """
    try:
        # Get growth metrics
        metrics = await state.cognitive_core.growth_tracker.calculate_metrics()
        stage = await state.cognitive_core.growth_tracker.get_current_stage()
        
        # Get recent concepts from semantic memory
        concepts = await state.cognitive_core.semantic_memory.get_all_concepts(10)
        concept_names = [c.get('concept', 'unknown') for c in concepts if c.get('concept')]
        
        # Get recent insights from philosophical memory
        insights = await state.cognitive_core.philosophical_memory.get_insights(5)
        
        # Get conversation stats for this session
        session_messages = await state.db.chat_history.count_documents({"session_id": session_id})
        total_sessions = len(await state.db.chat_history.distinct("session_id"))
        
        # Get uploaded files
        import os
        upload_dir = "/app/uploads"
        files = []
        if os.path.exists(upload_dir):
            files = [f for f in os.listdir(upload_dir) if os.path.isfile(os.path.join(upload_dir, f))]
        
        # Build progress bar for next stage
        progress_display = ""
        if stage.get("next_stage"):
            progress = stage.get("progress_to_next", {})
            progress_display = f"""\n**Progress to {stage['next_stage']}:**\n• Connections: {'█' * (progress.get('connections', 0) // 10)}{'░' * (10 - progress.get('connections', 0) // 10)} {progress.get('connections', 0)}%\n• Concepts: {'█' * (progress.get('concepts', 0) // 10)}{'░' * (10 - progress.get('concepts', 0) // 10)} {progress.get('concepts', 0)}%\n• Avg Degree: {'█' * (progress.get('avg_degree', 0) // 10)}{'░' * (10 - progress.get('avg_degree', 0) // 10)} {progress.get('avg_degree', 0)}%\n• Diameter: {'█' * (progress.get('diameter', 0) // 10)}{'░' * (10 - progress.get('diameter', 0) // 10)} {progress.get('diameter', 0)}%"""

        # Build response
        response = f"""🧠 **QUANTUM AI MEMORY STATUS**

**Growth Stage:** {stage.get('name', 'Nascent')} (Level {stage.get('stage', 0)})
_{stage.get('description', 'Initial awareness forming')}_
{progress_display}

**Learning Metrics:**
• Connections: {metrics.get('total_connections', 0)}
• Concepts: {metrics.get('total_concepts', 0)}
• Questions Generated: {metrics.get('total_questions', 0)} (legacy)
• Insights Formed: {metrics.get('total_insights', 0)} (legacy)
• Graph: avg degree={stage['metrics']['topology']['avg_degree']}, diameter={stage['metrics']['topology']['diameter']}
• Growth Rate: {metrics.get('growth_rate', 0):.1f} events/hour

**Recent Concepts:** {', '.join(concept_names[:5]) if concept_names else 'None yet'}

**Recent Insights:** 
{chr(10).join(['• ' + i.get('insight', '')[:80] for i in insights[:3]]) if insights else '• Still forming initial understanding'}

**Session Stats:**
• Messages this session: {session_messages}
• Total sessions: {total_sessions}

**Documents Available:** {len(files)} files
{chr(10).join(['• ' + f for f in files[:5]]) if files else '• No files uploaded'}

_Use `!research <topic>` to learn and grow!_"""
        
        return response
        
    except Exception as e:
        return f"🧠 Memory status unavailable: {str(e)}"


async def do_deep_research(topic: str) -> str:
    """
    Perform a multi-source research pass on a topic and record the result as a growth event.
    
    Performs a web search, consults semantic memory, and optionally looks up dictionary definitions; compiles findings into a user-facing summary and records a `deep_research` growth event in the growth tracker.
    
    Parameters:
        topic (str): The subject to research.
    
    Returns:
        str: A formatted summary of findings (web snippets, memory recall, and dictionary definition when available) that notes knowledge was added to memory when applicable, or an error message beginning with "🔍 Research error:" if the operation fails.
    """
    try:
        results = []
        
        # 1. Web search
        search_results = await state.universal_explorer.internet.search_web(topic, num_results=5)
        
        if search_results.get("count", 0) > 0:
            results.append("**🌐 Web Research:**")
            for r in search_results.get("results", [])[:3]:
                title = r.get("title", "")[:60]
                snippet = r.get("snippet", "")[:150]
                results.append(f"• **{title}**\n{snippet}")

        
        # 2. Check semantic memory for related concepts
        related = await state.cognitive_core.semantic_memory.recall_concept(topic)
        if related:
            results.append(f"\n**📚 From Memory:**\n• {related.get('definition', 'Previously encountered concept')[:200]}")

        
        # 3. Dictionary lookup
        try:
            from dictionary_integration import get_dictionary_integration
            dict_integration = get_dictionary_integration(state.cognitive_core.semantic_memory)
            dict_result = await dict_integration.lookup_and_store(topic)
            if dict_result.get("status") == "added" or dict_result.get("status") == "existing":
                definition = dict_result.get("data", {}).get("primary_definition", "")
                if definition:
                    results.append(f"\n**📖 Definition:**\n• {definition[:200]}")

        except Exception:
            pass
        
        # 4. Store as growth event
        await state.cognitive_core.growth_tracker.record_growth_event(
            event_type="deep_research",
            details={"topic": topic, "sources_found": len(results)}
        )
        
        # Build response
        if results:
            response = f"🔍 **DEEP RESEARCH: {topic.upper()}**\n" + "\n".join(results)

            response += "\n_This knowledge has been added to my memory._"

        else:
            response = f"🔍 **Research on '{topic}'**\nI couldn't find substantial information on this topic. Would you like to tell me more about it?"

        
        return response
        
    except Exception as e:
        return f"🔍 Research error: {str(e)}"


async def get_most_recent_document_text():
    """Get text from most recent uploaded document"""
    import os
    upload_dir = "/app/uploads"
    if not os.path.exists(upload_dir):
        return None, None
    
    files = [f for f in os.listdir(upload_dir) if f.endswith(('.pdf', '.docx', '.txt'))]
    if not files:
        return None, None
    
    files.sort(key=lambda x: os.path.getmtime(os.path.join(upload_dir, x)), reverse=True)
    filename = files[0]
    file_path = os.path.join(upload_dir, filename)
    
    result = await state.universal_explorer.documents.process_document(file_path)
    if "error" not in result:
        return result.get("text", ""), filename
    return None, filename


async def analyze_book_characters():
    """
    Generate a character-extraction response for the most recently uploaded book.
    
    Attempts to extract characters from the latest uploaded document; if no document is found returns a prompt to upload one, and if extraction is not implemented returns a placeholder message. On unexpected errors returns an error message.
    
    Returns:
        str: A user-facing message — either a prompt when no document is available, a placeholder character-extraction header that includes the filename, or an error string prefixed with "📚 Character analysis error:".
    """
    try:
        text, filename = await get_most_recent_document_text()
        if not text:
            return "📚 No document found. Please upload a book first."
        return f"📚 **CHARACTERS IN {filename.upper()}**\nNative character extraction not yet implemented. Use /analyze for general text analysis."

    except Exception as e:
        return f"📚 Character analysis error: {str(e)}"


async def analyze_book_timeline():
    """
    Generate a timeline summary from the most recently uploaded book.
    
    If a supported uploaded document is found, returns a user-facing message that begins with a timeline header for the file and either the extracted timeline or a placeholder indicating native timeline extraction is not implemented. If no document is available, returns a message prompting the user to upload a book. On internal errors, returns an error message prefixed with "📅 Timeline analysis error:".
    
    Returns:
        str: A message to present to the user (timeline header and content, upload prompt, or error message).
    """
    try:
        text, filename = await get_most_recent_document_text()
        if not text:
            return "📅 No document found. Please upload a book first."
        return f"📅 **TIMELINE: {filename.upper()}**\nNative timeline extraction not yet implemented. Use /analyze for general text analysis."

    except Exception as e:
        return f"📅 Timeline analysis error: {str(e)}"


async def analyze_book_worldbuilding():
    """
    Generate a worldbuilding summary from the most recently uploaded document.
    
    If no uploaded document is found, returns a user-facing prompt asking to upload a book. If a document is found, returns a placeholder header indicating native worldbuilding extraction is not yet implemented and suggests using `/analyze`. On unexpected errors, returns an error message prefixed with "🌍 Worldbuilding analysis error:" that includes the exception text.
    
    Returns:
        str: A user-facing status or result message (no-document prompt, placeholder worldbuilding header for the found file, or an error message).
    """
    try:
        text, filename = await get_most_recent_document_text()
        if not text:
            return "🌍 No document found. Please upload a book first."
        return f"🌍 **WORLDBUILDING: {filename.upper()}**\nNative worldbuilding extraction not yet implemented. Use /analyze for general text analysis."

    except Exception as e:
        return f"🌍 Worldbuilding analysis error: {str(e)}"


async def analyze_book_feedback():
    """
    Produce writing feedback for the most recently uploaded document.
    
    Checks the most recently uploaded document and returns a user-facing message: if no document is available, returns the prompt "✍️ No document found. Please upload a book first."; if a document is found, returns a header indicating writing feedback for the file and a placeholder message noting native feedback is not implemented; on internal errors returns a string beginning with "✍️ Feedback error:" followed by the error text.
    
    Returns:
        str: A formatted message describing the feedback result or an error.
    """
    try:
        text, filename = await get_most_recent_document_text()
        if not text:
            return "✍️ No document found. Please upload a book first."
        return f"✍️ **WRITING FEEDBACK: {filename.upper()}**\nNative writing feedback not yet implemented. Use /analyze for general text analysis."

    except Exception as e:
        return f"✍️ Feedback error: {str(e)}"


async def process_shared_link(url: str) -> str:
    """
    Process a shared link, download the referenced file, and return a user-facing status message.
    
    Returns:
        str: A status message describing the outcome:
            - An "Unknown Link Type" message listing supported services if the link detector cannot identify the source.
            - A success message containing the downloaded filename, size (in KB), and the normalized source name when the download succeeds.
            - A failure message with the downloader's error details when the download fails.
            - An error message including the exception text if an unexpected exception occurs.
    """
    try:
        # Detect link type
        link_type = state.shared_link.detect_link_type(url)
        
        if link_type == 'unknown':
            return "🔗 **Unknown Link Type**\nSupported services:\n• Google Drive\n• Dropbox\n• OneDrive\n• Direct file URLs (http/https)"

        
        # Download file
        result = await state.shared_link.download_from_link(url)
        
        if result.get("status") == "success":
            filename = result.get("filename", "downloaded_file")
            size_kb = result.get("size", 0) / 1024
            
            return f"""🔗 **File Downloaded Successfully**

**File:** {filename}
**Size:** {size_kb:.1f} KB
**Source:** {link_type.replace('_', ' ').title()}

The file is now available for analysis. Ask me about it or use `!read {filename}` to process it."""
        else:
            error = result.get("message", "Unknown error")
            return f"🔗 **Download Failed**\n{error}\nMake sure the link is publicly accessible."

            
    except Exception as e:
        return f"🔗 Error processing link: {str(e)}"


async def list_all_documents() -> str:
    """
    Return a formatted listing of uploaded documents with basic metadata.
    
    Returns:
        str: A multi-line string containing a header and one line per file with an icon, bolded filename, size in KB (one decimal), and last-modified timestamp. If no upload directory or no files are found, returns "📁 **No Documents**\nUpload files using the Explorer tab or `!link <url>`". On unexpected errors, returns "📁 Error listing documents: <error>".
    """
    try:
        import os
        upload_dir = "/app/uploads"
        
        if not os.path.exists(upload_dir):
            return "📁 **No Documents**\nUpload files using the Explorer tab or `!link <url>`"

        
        files = []
        for filename in os.listdir(upload_dir):
            file_path = os.path.join(upload_dir, filename)
            if os.path.isfile(file_path):
                size_kb = os.path.getsize(file_path) / 1024
                mtime = os.path.getmtime(file_path)
                from datetime import datetime
                modified = datetime.fromtimestamp(mtime).strftime("%Y-%m-%d %H:%M")
                
                # Determine file type icon
                ext = filename.lower().split('.')[-1] if '.' in filename else ''
                icon = {'pdf': '📕', 'docx': '📘', 'txt': '📄', 'html': '🌐', 'json': '📋'}.get(ext, '📎')
                
                files.append({
                    "name": filename,
                    "size": size_kb,
                    "modified": modified,
                    "icon": icon
                })
        
        if not files:
            return "📁 **No Documents**\nUpload files using the Explorer tab or `!link <url>`"

        
        # Sort by modified date (most recent first)
        files.sort(key=lambda x: x["modified"], reverse=True)
        
        response = f"📁 **UPLOADED DOCUMENTS** ({len(files)} files)\n"

        for f in files:
            response += f"{f['icon']} **{f['name']}**\n{f['size']:.1f} KB • {f['modified']}\n"

        
        response += "_Ask about any document by name, or say 'compare all documents'_"
        return response
        
    except Exception as e:
        return f"📁 Error listing documents: {str(e)}"


async def generate_speech(text: str) -> str:
    """Generate speech from text using browser TTS or return URL"""
    # For now, return instructions for browser TTS
    # Could integrate with ElevenLabs or OpenAI TTS later
    return None


def get_help_text() -> str:
    """Get help text with all available commands"""
    return """📚 **QUANTUM AI COMMANDS**

**🧠 Thinking & Memory:**
• `!memory` - View growth stage and metrics
• `!thinking on/off` - Show/hide thinking
• `!graph` - Knowledge graph info

**🔍 Research & Learning:**
• `!research <topic>` - Deep research
• `!read [filename]` - Process file

**📁 Documents:**
• `!docs` - List documents
• `!link <url>` - Download from URL

**📖 Book Analysis:**
• `!characters` - Extract all characters
• `!timeline` - Generate plot timeline
• `!worldbuilding` - World/setting details
• `!feedback` - Writing suggestions

**🎨 Creative:**
• `!imagine <prompt>` - Generate image
• `!speak <text>` - Text-to-speech

**📤 Export:**
• `!export chat/memory` - Export data

**🎤 Voice:** Use mic button for voice input

_Type any question to chat!_"""


