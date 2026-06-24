---
type: note
title: Multimodal Agents
status: evergreen
created: 2026-01-05
updated: 2026-06-19
tags: [multimodal, computer-use, vision-language-models, voice-agents, document-understanding, vlm]
aliases: [vision agents, computer use agents]
---

Multimodal agents process and act across vision, audio, and documents through unified reasoning loops — enabling computer use, voice assistants, and document extraction with no need for underlying APIs. The 2024–2025 breakthrough is unified agent workflows where visual, audio, and text signals feed the same LLM reasoning step.

**Four modality patterns:**

1. **Computer Use** — Agent captures a screenshot, identifies UI elements, executes mouse/keyboard actions, then verifies with another screenshot. Claude Computer Use and OpenAI Operator (CUA) work with any application without API access. SeeAct achieves 51.1% on WebArena; Claude Opus 4.5 scores 77.8% on MMMU. Combine visual grounding with the accessibility tree for 75% better click accuracy.

2. **Voice Agents (Realtime Audio)** — OpenAI Realtime API and Gemini Live enable speech-to-speech with function calling over WebRTC (browser, lowest latency) or WebSocket (server/phone). VAD (voice activity detection, threshold ~0.5, silence 500ms) handles turn-taking. Falls back to text on transcription failure.

3. **Document Understanding (LlamaParse, Unstructured.io)** — VLMs replace OCR pipelines. Traditional OCR loses layout; VLMs understand multi-column tables, charts, and handwritten content. LlamaParse achieves highest accuracy at ~6s/page (vs OCR ~1s/page). Reuse uploads via the Files API across multiple queries to get 3–5x cost reduction.

4. **Image Generation** — DALL-E 3 (`dall-e-3` model) auto-enhances prompts, costs $0.04–0.12/image, supports `vivid`/`natural` style presets.

**Model benchmarks (2025):** GPT-4o: 84.2% MMMU; Claude Opus 4.5: 77.8% MMMU, best-in-class computer use; Gemini 2.5 Pro: SOTA on MMMU-Pro (81%) and video understanding (87.6%).

**Cost control:** resize screenshots to 1568×1568 before sending (50–70% token cost reduction); cache document uploads; vision tokens are 5–10x more expensive than text. Vision adds 1–3s latency per step — do not use if API access is available or real-time sub-500ms is required.

Part of [[advanced]].

Related: [[tool-definition]] · [[tool-calling]] · [[rag-architectures]] · [[code-generation-agents]] · [[agent-fundamentals]] · [[context-management]] · [[chunking-strategies]]
