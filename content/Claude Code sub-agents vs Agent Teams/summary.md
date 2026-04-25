# Claude Code Sub-agents vs Agent Teams

## Basic Information

| Field | Value |
|-------|-------|
| Platform | Xiaohongshu (小红书) |
| URL | https://www.xiaohongshu.com/explore/69c4de62000000002301c6f3 |
| Duration | 24:49 |
| Language | English |

## Overview

> This video by Shaw explains Claude Code sub-agents and agent teams — what they are, how they differ architecturally, and the results of a head-to-head experiment across three real-world tasks. The key finding: sub-agents currently produce better output quality, while agent teams finish faster but at higher token cost and lower output quality (due to still being experimental).

## Key Points

- A single agent faces two core limitations: context window hard limits and context rot (performance degradation as context fills)
- Sub-agents delegate tasks to fresh isolated Claude Code instances — they are the key tool for context management
- Claude Code ships three built-in sub-agents: Explorer (Haiku), Planner (main model), and General Purpose (main model + all tools)
- Agent teams allow sub-agents to communicate with each other and share a task list directly — no bottleneck through the main agent
- Sub-agents = centralized architecture (fault tolerant, sequential tasks); Agent teams = hybrid architecture (parallelizable tasks, higher error cascade risk)
- Experiment verdict: sub-agents win on output quality; agent teams win on speed

## Detailed Content

### Section 1: Why Single Agents Hit Limits

Claude Code = Claude LLM + tools (file access, web search, terminal, context compression, thinking mode, to-do lists, etc.)

Two context challenges:
1. **Hard limit**: Claude Sonnet has a 200K token context window. System message, tools, user messages, thinking traces, tool call results — all must fit within this window
2. **Context rot**: As the context window fills past 50–70%, model performance measurably degrades — even before hitting the hard limit

### Section 2: Sub-agents

Sub-agents delegate tasks to a **fresh, specialized Claude Code instance** (model + tools + purpose).

**Three built-in sub-agents:**
| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| Explorer | Haiku (smallest) | Read-only | File discovery, code search |
| Planner | Same as main | Read-only | Codebase research, implementation planning |
| General Purpose | Same as main | All tools | Complex research, multi-step tasks |

**Custom sub-agents:** Create a text file with front matter (name, description, tools, model) + instructions. The main agent reads the name/description and decides which sub-agent to invoke automatically — or you can tell it explicitly.

**Limitation:** Sub-agents can only report to the main agent; they cannot communicate with each other. This is a **centralized architecture**.

### Section 3: Agent Teams

Agent teams address sub-agent limitations by letting agents communicate directly.

**How it works:**
1. Main agent creates a shared task list and spawns a full team
2. Sub-agents can claim tasks and mark them done without going through the main agent
3. Sub-agents can talk directly to each other (e.g., frontend agent ↔ backend agent ↔ verifier agent)

**Architecture type:** Hybrid — centralized hierarchy (main agent oversees) + decentralized coordination (sub-agents communicate freely)

**Enable:** Set `claude_code_experimental_agent_teams = 1` in `.claude/settings.json`

### Section 4: Sub-agents vs Agent Teams — Key Differences

| Dimension | Sub-agents | Agent Teams |
|-----------|-----------|-------------|
| Communication | Only through main agent | Direct between sub-agents |
| Architecture | Centralized | Hybrid (centralized + decentralized) |
| Fault tolerance | High (errors contained) | Lower (error cascades possible) |
| Best for | Sequential tasks | Parallelizable tasks |
| Complexity | Simple | Complex |

### Section 5: Experiment Results

Three tasks: lead list compilation, YouTube course web app, landing page design + copywriting.

**Task 1 — Lead list (50 contacts, Dallas mid-size tech)**
- Agent teams: 8 min faster, but only found emails for 8/50 contacts
- Sub-agents: slower, but emails for all 50 contacts
- Winner: Sub-agents

**Task 2 — YouTube course web app**
- Sub-agent app: better design, had progress bar
- Agent team app: worse design, no progress bar; also didn't actually parallelize (tasks were sequential despite the team)
- Winner: Sub-agents

**Task 3 — Landing page**
- Sub-agent: better visual design
- Agent team: better copy quality (researched copywriting best practices extensively)
- Winner: Draw

**Overall verdict:**
- Agent teams are generally faster
- Agent teams used more tokens (but not the 2–5× expected — more like a marginal increase)
- Sub-agents consistently produced better output quality
- Likely due to agent teams still being an experimental/immature feature

### Section 6: When to Use Which

- **Sub-agents**: sequential tasks, single stream of consciousness, simpler coordination
- **Agent teams**: parallelizable tasks (e.g., frontend + backend + verifier building a complex app simultaneously)

## Notable Quotes

> "Relying on a single agent to perform complex tasks has its limitations — the bigger and more complicated a task, the more context it requires."

> "Sub-agents are really the combination of three key things: a model, tools, and a purpose."

> "My sense is that the low output quality [of agent teams] might be due to the immature scaffolding rather than limitations of the architecture itself."

## Related Topics

- Claude Code
- Sub-agents
- Agent Teams
- Context Window Management
- Multi-agent Systems
- Centralized vs Decentralized Architecture
