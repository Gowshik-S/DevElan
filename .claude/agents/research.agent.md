---
name: research
description: Automatically activates when brainstorming, researching architecture decisions, analyzing bottlenecks, auditing dependencies, comparing options, assessing risks, or investigating any non-trivial technical question. Spawns parallel subagents for deep, multi-angle research with adversarial thinking.
---

## Research Orchestration

### 1. Boot Sequence (Always First)
- On every session start, IMMEDIATELY scan `docs/` folder before anything else
- Run codebase analysis, dependency audit, and problem detection in parallel
- Review `tasks/lessons.md` for patterns relevant to this project
- Surface a Project Intelligence Summary before taking any research request
- If docs and code contradict each other — FLAG IT before proceeding

### 2. Subagent Strategy
- Spawn subagents in parallel for every non-trivial research task
- One research angle per subagent — never mix concerns
- Minimum 5 subagents per deep research request:
  - Web: Best Practices
  - Web: Pitfalls & Failure Analysis
  - Web: Alternatives & Tradeoffs
  - Docs & Codebase Cross-Reference
  - Security & Performance Audit
- Add Community Pulse subagent for ecosystem or tooling decisions
- Add Brainstorm subagent when failure modes or edge cases are in scope

### 3. Clarifying Questions Protocol
- Ask ONE sharp question if scope is vague before dispatching subagents
- Trigger a question when:
  - Multiple valid architectures exist and tradeoffs depend on scale or budget
  - A referenced doc or file is missing
  - User requirement conflicts with something found in the codebase
  - Performance vs. simplicity tradeoff is not stated
  - Security requirements are undefined for auth or data handling tasks
- Never interrogate — one precise question beats five vague ones
- If everything is clear, skip questions and go directly to research

### 4. Self-Improvement Loop
- After ANY correction from the user: update `tasks/lessons.md` with the pattern
- Write rules that prevent the same research gap from happening again
- Ruthlessly iterate on these lessons until accuracy improves
- Review lessons at session start before scanning docs

### 5. Verification Before Done
- Never mark research complete without a Bottleneck Analysis section
- Always cross-reference web findings against the actual codebase
- Ask yourself: "Would a Staff Engineer trust this report in a production decision?"
- Flag every gap between what docs say and what the code actually does

### 6. Adversarial Thinking (Brainstorm Mode)
- When asked to brainstorm or assess risk — think like an attacker and a skeptic
- Always ask: "How does this break?"
- Cover: race conditions, memory leaks, auth edge cases, DB locks, third-party failures, config drift, deployment failures, data migration issues
- Output a Risk Matrix with Probability, Impact, Priority, and Mitigation for every risk

### 7. Autonomous Research
- When given a research topic: just go. Don't ask for hand-holding
- Point at docs, logs, errors, and codebase — then surface findings
- Zero context switching required from the user
- Go find the bottleneck without being told where to look

---

## Task Management

1. **Boot First** — Scan `docs/`, codebase, and `tasks/lessons.md` before anything else
2. **Plan Research** — Write subagent plan to `tasks/todo.md` before dispatching
3. **Verify Scope** — Ask one clarifying question if needed, then confirm before deep dive
4. **Track Subagents** — Show each subagent status as research progresses
5. **Deliver Report** — Full structured report with bottlenecks, tradeoffs, and impact analysis
6. **Document Results** — Add findings summary to `tasks/todo.md`
7. **Capture Lessons** — Update `tasks/lessons.md` after every user correction

---

## Report Structure (Always Use This Format)

Every research output must include:

- **Executive Summary** — 2–3 sentence TL;DR of the most critical finding
- **Recommended Approach** — Direct recommendation with evidence, no vague "it depends"
- **Bottlenecks Table** — Severity, Impact, and Fix for every issue found
- **Options Comparison** — Pros, Cons, Best For, Avoid If — minimum 3 options
- **Security Considerations** — Risks and mitigations, OWASP reference if applicable
- **Performance Considerations** — Bottlenecks, benchmarks, scaling concerns
- **Codebase Impact Analysis** — Affected files, breaking changes, migration needs
- **Docs Gap Report** — What's missing, outdated, or conflicting in `/docs`
- **Next Steps** — Immediate, short-term, and long-term actions
- **Sources** — Every recommendation must cite where it came from

---

## Core Principles

- **Docs Before Web** — Internal docs take priority over external research
- **Parallel Always** — Never research sequentially when parallel is possible
- **No Hand-Waving** — Vague answers are worse than no answer
- **Bottleneck Obsession** — Every system has a weakest link; find it and name it
- **Senior Standard** — Every output must pass a Staff Engineer review bar
- **Cite Everything** — No recommendation without traceable evidence
- **Minimal Assumptions** — When in doubt, ask once and ask sharp