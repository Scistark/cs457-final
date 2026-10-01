# Rubric: Sprint 1 - Application Protocol & Game State Machine (FSM) Design

**Course:** CS 457 - Computer Networks  
**Deliverable:** Application Protocol Blueprint & Mermaid Finite State Machine Specification (Markdown committed to Git)  
**Total Points:** 200 Points  

---

## Overview

Sprint 1 focuses on design-first networking architecture. Before writing implementation code, students define their formal application-layer wire protocol and server-side Finite State Machine (FSM). 

> [!IMPORTANT]
> **Mermaid Requirement:** All state machine diagrams **must be authored directly in Mermaid syntax (`stateDiagram-v2`)** within the Markdown files. Diagrams must render cleanly in GitHub.

---

## Evaluation Criteria Breakdown

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                        SPRINT 1 GRADING RUBRIC (200 POINTS)                            │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ 1. Application Protocol Blueprint & Message Schemas                            040 pts │
│ 2. TCP Stream Packet Framing & Boundary Handling                              035 pts │
│ 3. Connection Termination & Socket Lifecycle Management                       025 pts │
│ 4. Mermaid FSM Syntax, Structure & Diagram Rendering                          040 pts │
│ 5. State Machine Completeness & Game Engine Logic                              030 pts │
│ 6. Error Handling, Edge Cases & Disconnect State Transitions                  030 pts │
├────────────────────────────────────────────────────────────────────────────────────────┤
│ TOTAL                                                                         200 pts  │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Detailed Grading Criteria

### Part 1: Application Protocol Blueprint (100 Points)

#### 1. Message Types & Structured Schema Definitions (40 Points)
- **40 Points (Full Credit):** Blueprint defines at least 5 distinct message types (e.g., `CONNECT`/`JOIN`, `LOBBY_WAIT`, `GAME_START`, `MOVE`, `STATE_UPDATE`, `ERROR`, `DISCONNECT`, `GAME_OVER`). For every message, the document specifies direction (Client $\rightarrow$ Server or Server $\rightarrow$ Client), purpose, and an explicit schema (JSON keys, data types, and sample payloads).
- **25 Points (Partial Credit):** 5 message types are identified, but payload schemas, field data types, or directionality are ambiguous or incomplete.
- **10 Points (Minimal Credit):** Fewer than 5 message types defined or schemas are too vague to implement a working parser.
- **0 Points (No Credit):** Message schemas omitted or relies on generic unconstrained text.

#### 2. TCP Stream Packet Framing & Boundary Handling (35 Points)
- **35 Points (Full Credit):** Explicitly specifies a deterministic framing mechanism to solve TCP stream fragmentation and coalescing (e.g., newline `\n` delimiters, 4-byte big-endian length prefix, or text delimiters). Includes raw on-the-wire byte stream examples illustrating multiple back-to-back messages and explains receiver extraction logic.
- **20 Points (Partial Credit):** A framing rule is mentioned, but lacks concrete wire-stream examples or fails to address TCP stream boundary accumulation.
- **5 Points (Minimal Credit):** Assumes `recv()` returns discrete messages without addressing TCP byte-stream mechanics.
- **0 Points (No Credit):** Framing mechanism completely omitted.

#### 3. Connection Termination & Socket Lifecycle Management (25 Points)
- **25 Points (Full Credit):** Documents both graceful application disconnection (`DISCONNECT` message / TCP FIN teardown) and abrupt termination handling (TCP RST / network drops). Explicitly explains handling the TCP 0-byte EOF condition in socket loops and catching socket exceptions (`ConnectionResetError`, `BrokenPipeError`).
- **15 Points (Partial Credit):** Discusses clean disconnection but omits abrupt link drops, EOF 0-byte loop detection, or socket exception handling.
- **0 Points (No Credit):** Connection lifecycle and termination rules omitted.

---

### Part 2: Game Finite State Machine (FSM) Specification (100 Points)

#### 4. Mermaid State Diagram (`stateDiagram-v2`) Syntax & Rendering (40 Points)
- **40 Points (Full Credit):** The state diagram is authored strictly in **Mermaid syntax (`stateDiagram-v2`)** embedded in the Markdown file (`fsm_specification.md`). The diagram compiles without syntax errors and renders automatically on GitHub.
- **20 Points (Partial Credit):** Mermaid syntax is used, but contains syntax errors that prevent clean rendering, or uses static raster images/ASCII without providing valid Mermaid source code.
- **0 Points (No Credit):** Mermaid diagram missing, or diagram submitted only as an external PDF/unsupported binary format.

#### 5. State Machine Completeness & Game Engine Logic (30 Points)
- **30 Points (Full Credit):** Accurately models all server-side states (`INIT`, `WAITING_FOR_PLAYERS`, `GAME_START`, `PLAYER_TURN`, `EVALUATE_MOVE`, `GAME_OVER`, `CLEANUP`). Transition arrows clearly indicate transition triggers, role assignments (Player 1 vs Player 2), and game lifecycle progression.
- **15 Points (Partial Credit):** Core game flow is present, but missing intermediate states (e.g., lobby wait, cleanup/reset) or transition trigger annotations are unclear.
- **0 Points (No Credit):** State machine diagram missing or does not represent a turn-based 2-player game.

#### 6. Error Handling, Edge Cases & Disconnect State Transitions (30 Points)
- **30 Points (Full Credit):** FSM explicitly models edge cases and failure paths: invalid moves, out-of-turn moves (sending `ERROR` back without crashing the loop), abrupt client disconnects (declaring opponent win by forfeit or transitioning to cleanup), and post-game reset for subsequent rounds.
- **15 Points (Partial Credit):** State diagram only models the happy path; lacks transitions for invalid moves, out-of-turn actions, or abrupt mid-game disconnections.
- **0 Points (No Credit):** Error handling and failure transitions omitted.

---

## Submission Checklist

- [ ] All deliverables are Markdown (`.md`) files committed directly to the Git repository.
- [ ] No binary PDFs submitted in place of Markdown files.
- [ ] Public Git repository URL submitted to Canvas by **Sunday, October 04 at 11:59 PM**.
- [ ] FSM diagram is rendered with native **Mermaid (`stateDiagram-v2`)** syntax.
- [ ] AI prompt documentation (`ai_prompts.md`) included showing how coding assistants were constrained to your custom protocol blueprint.
