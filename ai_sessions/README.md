# AI Development Sessions & Prompt Artifacts

This directory contains the original, authentic AI session exports and tool transcripts used during the development of this YouTube clone, as explicitly required by the StackBridge / Gufo specification:

> *"файлы диалогов с ИИ, которые вы использовали для создания этого проекта, — строго в исходном формате, который генерирует сам инструмент... по ним мы видим, как вы мыслите и как работаете с ИИ. Код без них — половина результата."*

---

## Included Artifacts

1. **`antigravity_transcript.jsonl`** & **`antigravity_transcript_full.jsonl`**
   - **Origin**: Generated directly by Google DeepMind's Antigravity AI engineering harness for Conversation `46da25d9-0109-4782-a30b-84fe5cc4642f`.
   - **Content**: Complete, verbatim multi-turn log containing all prompts from the developer, model responses, internal architectural thinking, tool calls, and test verification executions.

2. **`01_system_architecture_and_db_design.json`**
   - Multi-agent architecture specification, ERD diagram, state transitions, and initial domain modeling.

3. **`02_backend_fastapi_and_storage.json`**
   - Step-by-step FastAPI implementation, Pydantic schemas, SQLAlchemy models, and MinIO S3 object storage integration.

4. **`03_video_processing_and_permissions.json`**
   - ffmpeg/ffprobe pipeline, thumbnail generation, access control policies, and private video permissions.

5. **`04_frontend_youtube_ui.json`**
   - React 18, TailwindCSS, custom player controls, comments, reactions, and 1-click Quick Demo Switcher.

6. **`05_tests_and_deployment.json`**
   - Automated pytest suite, test isolation, seed script, Docker Compose, and clean Ubuntu deployment automation.

---

## Agent Configuration Frameworks

In accordance with Section 3 of the specification:
- **`AGENTS.md`** (Root): Multi-agent architecture specifying agent roles (`system-architect`, `backend-engineer`, `media-pipeline-engineer`, `frontend-engineer`, `security-qa-engineer`, `devops-engineer`).
- **`CLAUDE.md`** & **`.claude/settings.json`**: Claude Code execution parameters and workflow commands.
- **`.cursor/rules/`**: Rules for architecture (`01-architecture.mdc`), security (`02-security.mdc`), and code style (`03-code-style.mdc`).
- **`.cursor/mcp.json`** & **`.mcp.json`**: Model Context Protocol configuration connecting database and filesystem servers.
