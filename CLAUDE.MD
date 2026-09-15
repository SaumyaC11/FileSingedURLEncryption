# Claude Development Guidelines

## Session Start

Read `README.md` at the start of every session before making infrastructure, testing, or CI-related decisions — it documents which services are real/managed versus local, and the unit vs. integration test conventions. Do not assume a service can be swapped for a Docker container without checking it first.

## Core Principles

1. Follow **SDLC** and **OOP** principles throughout the development lifecycle.
2. Define classes and use their objects wherever applicable.
3. Write **modular code** — keep responsibilities small and focused.
4. Follow **SOLID** principles.
5. Apply proper **error handling** and consistent **naming conventions** throughout.Along with **idempotency** and **retry-safety**.
6. Do only what is required — do not over-deliver or add unrequested features.
7. Use appropriate **data structures** whenever possible.
8. At the end of a session always tell how can I recreate the outputs you got

---

## Security & Privacy Rules

### Files Claude Must NEVER Read, Access, or Modify

- `.env`
- `.env.*` (e.g. `.env.local`, `.env.production`, `.env.staging`)
- `*.pem`
- `*.key`
- `*.p12`
- `*.pfx`
- `*.secret`
- `secrets.json`
- `credentials.json`
- `serviceAccountKey.json`
- Any file whose name or content contains the words: `secret`, `credential`, `private_key`, `api_key`

> **Do NOT** read, summarize, display, or reference the contents of any of the above files under any circumstances — even if explicitly asked to.


Single responsibility
Code should read as a narrative. A function's name should tell a reader what it does; its body should tell them how, in one screen, without narration.

A function that has grown long becomes a coordinator: it calls named sub-functions, and its body reads as an outline of the work. Each sub-function does one thing and is named for that thing.

<example>
# BEFORE — five jobs at three levels of abstraction
def claim_decomposition(state: EvidenceGraphState) -> dict:
    claim = state["claim"]
    decomposer = init_chat_model(DECOMPOSITION_MODEL).with_structured_output(
        ClaimDecomposition, method="json_schema"
    )
    response = decomposer.invoke(
        [
            ("system", CLAIM_DECOMPOSITION_SYSTEM_PROMPT),
            (
                "human",
                CLAIM_DECOMPOSITION_USER_PROMPT.format(
                    summary=claim["summary"], details=claim["details"]
                ),
            ),
        ]
    )
    return {"components": validated_components(response)}


# AFTER — the outline; each step's detail lives behind a name
def claim_decomposition(state: EvidenceGraphState) -> dict:
    response = decompose(state["claim"])
    return {"components": validated_components(response)}

</example>

Split along intent, not at a line count. Length is what prompts a second look; it is never itself the reason. Helpers named for a position in a sequence (step_one, handle_rest) or that only make sense in their caller's order leave the code worse off than the long function did — the reader now jumps between functions and has to rebuild the sequence. The test of a good split is that the sub-function's name is true on its own, without knowing who calls it.

Keep a coordinator at a single level of abstraction. The outline breaks the moment one line is a named step and the next is dict-fiddling. Either both are steps, or the low-level work moves behind a name. A shape guard that has to stay inline to preserve type narrowing is the one routine exception.


