---
title: Systems Engineering for AI Agents — FSMs and Minions for Production Reliability
description: A deep dive into Hyades' deterministic architecture, minion decomposition inspired by Starnet, and strict state and memory governance.
date: 2026-10-08
tags:
  - AI
  - Agents
  - FSM
  - Hyades
  - Starnet
  - Systems Architecture
  - Linux
---

# Systems Engineering for AI Agents — FSMs and Minions for Production Reliability

> **Project Status:** WIP / Active Development  
> **Author:** Enzo Zavorski Delevatti ([@Zvorky](https://github.com/Zvorky))  
> **Date:** October 2026  
> **Topics:** Systems Engineering, Autonomous Agents, Finite State Machines (FSM), Linux IPC, Model Context Protocol.

---

The software industry is experiencing a predictable hangover with AI agents.

Between 2023 and 2025 the ecosystem was flooded with frameworks promising full autonomy through very high-level abstractions over LLM calls. The common recipe was: instantiate an agent, plug in five tools, write an excited system prompt and let it "think".

In controlled three-minute demos everything looks magical. But the reality shock when putting these solutions into production is brutal: **between 40% and 60% of corporate agentic workflow executions fail**.

Failures rarely arise from the language model's intelligence. The bottleneck is purely systems engineering: delegating the application's control plan to a probabilistic process.

In this article I discuss why open loops collapse, how the concept of **minions** explored by [Starnet (androoAGI)](https://github.com/androoAGI/starnet) points to the right decomposition, and how I'm building **Hyades** — a deterministic orchestrator focused strictly on function and resource hardening rather than superficial aesthetics.

---

## 1. The Fundamental Problem: The "Semantic Von Neumann" and the Open ReAct Loop

In the classical von Neumann computer architecture, control instructions and data travel over the same physical memory bus — the historical root of vulnerabilities like Buffer Overflow and SQL Injection.

In contemporary transformer-based language models we suffer a semantic variation of the same dilemma: **inside the context window, operator instructions and untrusted external data share the same attention space.** There is no native token-level "Ring 0" hardware layer.

When popular frameworks (e.g., LangChain, CrewAI, or AutoGen) implement the ReAct (Reason + Act) pattern, they treat the agent lifecycle as an open while loop:

```
[User Input]
       │
       ▼
┌───────────────────────────────┐
│     Prompt with N Tools       │ ◄──────────┐
└──────────────┬────────────────┘            │
               │                             │
               ▼                             │ (Stochastic Loop)
┌───────────────────────────────┐            │
│  LLM Decides Next Step        │ ───────────┘
│  (and decides when to stop)   │
└──────────────┬────────────────┘
               │
               ▼
[Result or Flow Collapse]
```

If the model decides **what to do**, **which tool to call**, and **when the task is complete**, you introduce three inevitable failure modes:

1. **Lack of Determinism in Control Flow:** A temperature change or an unexpected external API response can make the model skip business validations and transition prematurely to completion.
2. **Tool-Calling Hallucination from Context Overload:** Exposing 10–20 tools at once in the prompt increases the probability that the model will call the wrong tool — or call it out of order — exponentially.
3. **Context Bleed:** The history of failed attempts, error messages and intermediate hallucinations pollutes the context window. The model begins to focus on its past mistakes, entering repeating loops that drain the token budget.

For an autonomous system to be reliable in production, a fundamental distributed-systems rule must be re-established: **the LLM must never govern the application's control flow.**

---

## 2. The Death of the Monolithic Agent: The Concept of Minions

One of the most interesting projects I studied recently is [**Starnet**](https://github.com/androoAGI/starnet), by androoAGI.

Starnet attacks the fallacy of the "monolithic agent." Rather than designing a single huge agent that reads the goal, decomposes the problem, calls dozens of tools, evaluates results and generates the response, it proposes segregation into **minions**.

A *minion* is a sub-agent:

- Disposable: has an ephemeral lifecycle and is instantiated only to solve an atomic subtask.
- Surgical scope: receives exclusively the context strictly necessary for that step (minimizing context bleed).
- Isolated: does not share volatile state directly with other minions; results are returned in a structured form.

However, splitting into minions becomes chaotic if their coordination is governed by another probabilistic loop. If the minions' manager is another LLM deciding on the fly who to call next, you have merely distributed stochastic chaos across multiple processes.

The missing piece to close this equation is the **Finite State Machine (FSM)**.

---

## 3. The Architectural Solution: Deterministic FSM + Capability Gates

The approach that turns this into production-grade engineering is to invert the control hierarchy. Deterministic software governs; the model only computes.

```
      ┌─────────────────────────────────────────┐
      │    Deterministic FSM (Rigid Code)       │
      │   Valid States and Strict Contracts     │
      └────────────────────┬────────────────────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
┌───────────────┐  ┌───────────────┐  ┌───────────────┐
│ State: PARSE  │  │ State: EVAL   │  │ State: EXEC   │
├───────────────┤  ├───────────────┤  ├───────────────┤
│ Capability:   │  │ Capability:   │  │ Capability:   │
│ [read_spec]   │  │ [calc_diff]   │  │ [write_db]    │
└───────┬───────┘  └───────┬───────┘  └───────┬───────┘
        │                  │                  │
        ▼                  ▼                  ▼
   (Minion LLM        (Minion LLM        (Minion LLM
    Pure Scope)         Pure Scope)         Pure Scope)
```

This architecture relies on three pillars:

### 1. Strict Code-Driven State Transitions

The execution pipeline is modeled as a directed acyclic graph (DAG) or an FSM with explicit transitions:

$$\text{State}_{n+1} = \delta(\text{State}_n, \text{Validated Event})$$

The LLM is invoked inside a state to perform a textual or structured transformation (e.g., extract data, generate code, summarize). Once the output returns, a schema validator (e.g., Pydantic) checks types. If the output validates, the **code** emits the event that transitions to the next state. The model does not know which state comes next.

### 2. Dynamic Capability Gates

In operating systems, kernels isolate privileged instructions via protection rings (Ring 0 vs Ring 3). In AI agents, the same principle translates to **Capability Gates**.

Each FSM state injects into the model context exclusively the tools allowed for that moment:

- In read-and-analyze states (`ANALYZING`), side-effecting tools (database writes, sending emails, executing bash commands) simply do not exist in the schema list sent to the model.
- Even if an agent is subject to an indirect prompt injection through a malicious document, the injection fails because destructive tools are physically absent in that state.

### 3. Atomic Local Persistence

Instead of relying on ephemeral arrays in process memory, every state transition, session goal and transcription must be recorded transactionally (using patterns such as SQLite in WAL mode). This allows freezing the process, inspecting history and resuming executions without state loss.

---

## 4. Inside Hyades: Building the Machine Room

**Hyades** is the project where I'm implementing these concepts in practice.

From the first commit I adopted a clear directive: **prioritize function over aesthetics 100%**. Before designing pretty interfaces or gradient-filled screens, the "machine room" — the process model, the state machine, memory management and data integrity — must be rock-solid.

Below I highlight the main architectural components already developed and tested in the repository:

### 4.1. Decoupled Core FSM and Transition Contracts

The heart of Hyades is an FSM engine decoupled from input interfaces. Each state has invariant contracts:

- Strict input and output schemas.
- Declarative Capability Gates that filter tools at runtime.
- Atomic exception handling with deterministic error-recovery fallback.

### 4.2. Background Daemon Architecture with Dedicated IPC

Rather than running as a monolithic script that blocks the terminal, Hyades operates as an independent daemon process (`hyades-daemon`).

- The daemon manages session lifecycles, the event pipeline, and communication with models.
- Control interfaces (a lightweight CLI, a terminal TUI or a web cockpit) connect to the daemon via a lightweight, asynchronous and decoupled IPC protocol.

### 4.3. Low-Level Resource Auditing: VmRSS via /proc

Many Python frameworks suffer silent memory leaks that are only noticed when the Linux OOM killer kills the container in production.

In Hyades the quality suite audits the process's real memory consumption by directly inspecting `VmRSS` (Virtual Memory Resident Set Size) metrics in `/proc/[pid]/status`:

- Avoids measurement distortion caused by `fork()` under concurrent test execution.
- Establishes strict memory footprint limits at rest and under continuous load.

### 4.4. Payload-Level Secret Masking and Redaction

One of the greatest risks when persisting full agent transcripts is inadvertent leakage of API keys, `sk-` tokens and passwords into log files or UI screens.

We implemented an event interceptor that operates at the payload layer:

- Known sensitive fields are replaced with security masks.
- Free-form strings pass through regex filters before being persisted to history or streamed via websocket to the UI.

### 4.5. Operational Interfaces: Textual TUI, CLI and Starlette Bridge

For operators the fastest interface is the terminal:

- Quick CLI: commands to trigger session goals and query state.
- TUI (Terminal User Interface): a reactive terminal interface built in Python with Textual, allowing operators to follow logs, FSM states and sessions in real time over SSH.
- Starlette Web Bridge: an asynchronous bridge layer exposing CSRF-protected routes for connection with a graphical interface (React SPA).

---

## 5. Architectural Comparison: Open Loop vs FSM Governance

| System Dimension | Traditional Frameworks (ReAct / Free Loop) | FSM-Governed Architecture (Hyades) |
| :--- | :--- | :--- |
| **Control Flow** | Stochastic (decided by the model) | Deterministic (rigid code) |
| **Tool Exposure** | Static (all tools in the prompt) | Dynamic (Capability Gates per state) |
| **Resilience to Injection** | Low (vulnerable to prompt deviations) | High (physical absence of dangerous tools) |
| **State Persistence** | Ephemeral / In-memory | Transactional (auditable SQLite WAL) |
| **Debugging / Rollback** | Black-box unpredictable | Traceable state-by-state transitions |
| **Resource Footprint** | Uncontrolled (context bloat) | Audited (VmRSS and memory limits) |

---

## 6. Current Status and Next Steps (Living Document)

Hyades remains in **active development and closed-source**.

My priority right now is stabilizing the CI pipeline, consolidating lint/formatting quality gates, and ensuring that memory and determinism invariants remain 100% hermetic under heavy stress testing.

This article is a **living document**. As I advance over the next development milestones — especially comparative throughput benchmarks, IPC protocol evolution and integration with local inference providers — I will update this text with metrics and additional implementation details.

Once the foundation is truly stable and battle-tested, the repository will be opened to the community.
