# Auto-Grounder (Self-Healing Output Pipeline)

Auto-Grounder is an automated remediation pipeline that closes the loop on AI hallucinations. It transforms passive hallucination *detection* into active, automated *correction*.

## Focus
Automation & AI Engineering (LLMOps).

## Core Features

1. **Automated Interception**
   - Hooks into the `truthguard-ai` verification pipeline. 
   - When a generated response is flagged as `CONTRADICTED` or given a `HIGH` hallucination risk score, Auto-Grounder intercepts the response instead of returning a failure to the user.

2. **Evidence-Based Remediation**
   - Takes the failed LLM response and the *trusted evidence* retrieved by `truthguard-ai`.
   - Constructs a corrective prompt (e.g., *"Your previous answer contained hallucinations. Rewrite the answer using ONLY the following trusted evidence..."*).
   - Resends this package to the LLM to generate a corrected response.

3. **Iterative Verification Loop**
   - Passes the newly generated answer back through the `truthguard-ai` pipeline.
   - Loops this process until the response achieves a `LOW` risk score or hits a predefined maximum retry limit.

## Why it Fits in GroundedAI
A complete AI platform doesn't just grade models; it fixes them. Auto-Grounder serves as the crucial automation layer that makes applications built on GroundedAI robust and self-healing.

## Proposed Architecture

```text
User Query ──► [ Initial LLM Generation ]
                      │
                      ▼
             [ truthguard-ai ] ◄──────────► [ Trusted Search/KB ]
                      │ (Extract Claims, Retrieve, Verify)
                      │
              Is Risk Score LOW?
               /              \
            YES                NO (Contradiction/Hallucination)
            /                    \
     Return to User               ▼
                          [ Auto-Grounder ]
                                  │ 1. Package failed answer + evidence
                                  │ 2. Apply corrective prompt
                                  ▼
                          [ Corrective LLM ] 
                                  │
                                  └─► (Loop back to truthguard-ai)
```

## Roadmap / Next Steps
- [ ] Define the interface connecting `truthguard-ai`'s output to `auto-grounder`.
- [ ] Design the corrective system prompt template.
- [ ] Implement the retry loop with a configurable maximum depth.
- [ ] Add tracking/logging so developers can see when and how often self-healing is triggered.
