# Prompt Shield (LLM Security Proxy)

Prompt Shield is a lightweight middleware/proxy service designed to intercept traffic between user applications and Large Language Models (LLMs). 

While other tools in the GroundedAI ecosystem focus on ensuring the LLM's outputs are factually grounded, **Prompt Shield** focuses on ensuring the user's inputs are safe and sensitive data is not leaked.

## Focus
Security, Data Privacy (PII), and Adversarial Defense.

## Core Features

1. **Prompt Injection & Jailbreak Detection**
   - Analyzes incoming user prompts for adversarial patterns designed to bypass system instructions.
   - Blocks known jailbreak signatures and suspicious semantic patterns before they reach the LLM.

2. **PII Scrubbing & Re-injection**
   - Automatically detects Personally Identifiable Information (SSNs, emails, phone numbers, API keys) using local NER (Named Entity Recognition) models or regex.
   - Replaces sensitive data with placeholders (e.g., `[EMAIL_1]`) before sending the prompt to external LLM APIs (like OpenAI or Anthropic).
   - Re-injects the real data back into the LLM's response before returning it to the user.

3. **Toxicity & Malicious Intent Filtering**
   - Uses fast, lightweight local models (e.g., ONNX-based sequence classifiers) to evaluate inputs and outputs for hate speech, harassment, or self-harm content.

## Why it Fits in GroundedAI
GroundedAI approaches AI safety from multiple angles:
- `truthguard-ai` ensures the LLM doesn't lie or hallucinate (Output/Factual Safety).
- `prompt-shield` ensures the user isn't malicious and enterprise data isn't leaked (Input/Security Safety).

## Proposed Architecture

```text
User Application 
       │
       ▼ (Raw Prompt)
[ Prompt Shield ] ── 1. Toxicity Check
       │          ── 2. Jailbreak Check
       │          ── 3. PII Redaction (Store mapping)
       ▼ (Sanitized Prompt)
     [ LLM ]
       │
       ▼ (Raw Response)
[ Prompt Shield ] ── 4. PII Re-injection
       │          ── 5. Output Toxicity Check
       ▼ (Safe Response)
User Application
```

## Roadmap / Next Steps
- [ ] Define the FastAPI proxy structure.
- [ ] Integrate a fast, local PII detection library (like Microsoft Presidio).
- [ ] Implement a basic heuristic/regex-based prompt injection detector.
- [ ] Create mock endpoints for testing the proxy locally.
