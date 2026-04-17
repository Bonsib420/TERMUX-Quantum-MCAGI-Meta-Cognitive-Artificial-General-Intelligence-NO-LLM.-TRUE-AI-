# Quantum MCAGI - Next Steps TODO List

Based on system analysis and the status documented in CLAUDE.md, here are the prioritized next steps:

## 🔴 **HIGH PRIORITY** (Immediate Impact)

### 1. Fix Conscious Moments Persistence
- **Issue:** Conscious moments counter increments but resets/stuck at 1 between responses
- **Location:** Likely in shared_state.py or quantum_cognitive_core.py
- **Action:** Trace where consciousness counter is stored and ensure it persists across requests
- **Impact:** Basic metric tracking would work correctly

### 2. Fix Double Question Generation Bug
- **Issue:** Questions generated twice (double-append bug)
- **Location:** Response pipeline - likely in chat.py or hybrid_generator.py
- **Action:** Find where questions are appended and prevent duplication
- **Impact:** Cleaner, more professional responses

### 3. Feed Hilbert Engine with Training Data
- **Issue:** Hilbert engine wired but needs training data
- **Action:** Run batch_ingest.py to train both Markov and Hilbert engines
- **Command:** `python batch_ingest.py` (may need parameters)
- **Impact:** Better semantic understanding and concept associations

### 4. Establish Reliable Cloud Backup
- **Issue:** Wolfram 502 errors, pCloud over quota, rclone not configured
- **Actions:**
  - Configure rclone for Google Drive or another service
  - Test manual upload as interim solution
  - Automate backup script
- **Impact:** Persistent knowledge base across sessions

### 5. Wire DevLog into System
- **Issue:** DevLog file exists but nothing imports/uses it
- **Action:** Add import and integration points in key modules (chat.py, shared_state.py)
- **Impact:** Better debugging and error tracking

## 🟡 **MEDIUM PRIORITY** (Quality Improvements)

### 6. Clean Junk Concepts from Knowledge Graph
- **Issue:** Concepts like "that", "facilitated", "then", "both" pollute the knowledge graph
- **Location:** Concept extraction pipeline (likely in hidden_thinking.py or domain_knowledge.py)
- **Action:** Add stopword filtering during concept ingestion
- **Impact:** Higher quality knowledge graph and associations

### 7. Implement Tone-Adaptive Chaos Probabilities
- **Issue:** Chaos engine uses static probabilities regardless of context
- **Location:** chaos_engine.py
- **Action:** Scale quote_probability and dream_probability based on tone_depth
- **Formula:** effective_prob = base_prob * (1.0 + tone_depth * 0.5)
- **Impact:** More appropriate philosophical responses for deep queries

### 8. Expand Dream Corpus with Cosmological Themes
- **Issue:** Dream injections lack relevance to deep philosophical topics
- **Location:** dream_state.py or associated dream corpus
- **Action:** Add fragments about cosmological collapse, creation-as-measurement, void-as-superposition
- **Impact:** More contextually relevant dream injections for philosophical queries

## 🟢 **LOWER PRIORITY** (Enhancements & Polish)

### 9. Fix Web UI Message Auto-Scroll
- **Issue:** Messages don't auto-scroll to latest response
- **Location:** frontend/src/components/ChatInterface.jsx or App.jsx
- **Action:** Add scroll-to-bottom logic when new messages arrive
- **Impact:** Better user experience

### 10. Fix Web UI Sidebar Toggle in Portrait Mode
- **Issue:** Sidebar toggle not working properly on mobile portrait
- **Location:** frontend/src/App.jsx CSS/media queries
- **Action:** Fix responsive breakpoints and toggle logic
- **Impact:** Improved mobile usability

### 11. Wire Image Generation Endpoint in Server.py
- **Issue:** Image generation endpoint exists but may not be fully integrated
- **Verification:** Already tested and working, but double-check registration
- **Impact:** Ensures reliability

### 12. Replace PMI Scoring with Hilbert Engine in Hybrid Generator
- **Issue:** Hybrid generator uses basic PMI, could use Hilbert space semantics
- **Location:** hybrid_generator.py
- **Action:** Integrate hilbert_bridge.py for concept associations
- **Impact:** More semantically coherent responses

### 13. Implement Quantum Sigil Visualization
- **Issue:** No visualization of Orch OR state during response generation
- **Location:** Frontend visualization component
- **Action:** Create component that displays quantum state evolution
- **Impact:** Educational and engaging feature showing the "quantum" processing

## 📊 **SYSTEM METRICS IMPROVEMENT**

### 14. Implement /grade Command for Rubric Scoring Automation
- **Issue:** No automated way to track response quality over time
- **Action:** Build /grade command that runs rubric scoring automatically
- **Location:** backend/routes_extras.py + frontend integration
- **Impact:** Quantitative tracking of system improvement

## 🔧 **TECHNICAL DEBT**

### 15. Resolve Linting Issues (Optional)
- **Note:** Pylint score is 9.16/10 - already excellent
- **Action:** Fix high-priority pylint warnings if desired
- **Impact:** Code quality maintenance

### 16. Address Bandit Security Warnings (Review Only)
- **Note:** Most are medium/low risk temp file usage and missing timeouts
- **Action:** Review critical ones (pickle usage, XML parsing) if handling untrusted input
- **Impact:** Security hardening (lower priority for local-only use)

## 🎯 **IMMEDIATE ACTION PLAN (Next 1-2 Sessions)**

**Session 1 Focus:**
1. [ ] Fix conscious moments persistence
2. [ ] Fix double question bug  
3. [ ] Feed Hilbert engine (run batch_ingest)
4. [ ] Wire DevLog into system

**Session 2 Focus:**
1. [ ] Establish cloud backup (rclone config)
2. [ ] Clean junk concepts from knowledge graph
3. [ ] Implement tone-adaptive chaos probabilities
4. [ ] Fix web UI auto-scroll

---

**VERIFICATION:** After each fix, test with:
```bash
curl -s http://localhost:8000/api/health
curl -s -X POST http://localhost:8000/api/quantum/chat -d '{"content":"test","explain_mode":false}'
```

**DOCUMENTATION:** Update TODO_NEXT_STEPS.md as items are completed.