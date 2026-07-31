# skill-agent

A self-improving agent experiment: does giving a small local LLM a **retrieved, focused set of tools** — instead of all tools at once — make it more reliable? Built from scratch on [smolagents](https://github.com/huggingface/smolagents), running fully offline on a CPU-only machine.

This is a learning + research project. The goal was not to build the best agent, but to **measure** how design choices affect a weak model's success rate, and to diagnose *why* things fail.

## TL;DR result

On a 5-task benchmark (5 runs per task, `qwen2.5:3b` via Ollama):

| Condition | Avg success |
|---|---|
| Baseline (all tools, no steering) | 52% |
| Retrieval only (no steering) | 40% — *retrieval hurt!* |
| Baseline + prompt steering | 76% |
| **Retrieval + prompt steering** | **84%** |

The headline finding: **retrieval alone made the agent worse**, until the real root cause — the model hallucinating tools leaked from the system prompt's examples — was fixed. Once fixed, focused retrieval *beat* the all-tools baseline.

## The question

A `CodeAgent` writes Python to call tools. When a small model has many tools (or is distracted by irrelevant ones), does it get confused? Hypothesis:

> If the agent is handed only the tools relevant to the current task, it will hallucinate less and succeed more often than an agent given every tool at once.

## Method

- **Model:** `qwen2.5:3b` served locally by Ollama, called via smolagents' `OpenAIServerModel` (OpenAI-compatible endpoint). CPU-only (integrated AMD GPU; Vulkan detected but not usable, documented below).
- **Tools:** three deterministic tools with fixed fake data (`get_employee_count`, `convert_currency`, `get_city_population`) so every task has a known, verifiable answer.
- **Retrieval:** each tool's description is embedded with `sentence-transformers` (`all-MiniLM-L6-v2`); the incoming task is embedded the same way; tools are ranked by cosine similarity and those above a threshold are handed to the agent.
- **Scoring:** exact-match after normalization (numbers compared as floats), never eyeballed.
- **pass@k:** every task is run 5 times and the **success rate** is reported, because the model is non-deterministic (identical inputs give different answers).

## Tasks

| Task | Needs | Tests |
|---|---|---|
| employees_combined | 1 tool, 2 lookups + add | basic tool use |
| currency_simple | 1 tool | picking the right tool |
| population_single | 1 tool | search-flavored temptation |
| two_tools | 2 lookups + arithmetic | multi-step composition |
| no_tool | none (`25 * 4`) | restraint / over-reaching |

## Results in detail

### Before steering

| Task | Baseline | Retrieval |
|---|---|---|
| employees_combined | 60% | 40% |
| currency_simple | 60% | 40% |
| population_single | 40% | 0% |
| two_tools | 0% | 20% |
| no_tool | 100% | 100% |
| **AVERAGE** | **52%** | **40%** |

Retrieval underperformed. Investigation showed the retriever was working correctly (e.g. the population task ranked `get_city_population` at 0.54, well clear of everything else) — the agent was simply **ignoring** the retrieved tool and hallucinating `web_search` / `wikipedia_search` / `import requests`, all of which appear in smolagents' default system-prompt examples. The most "search-flavored" task (population) failed hardest.

### After prompt steering

Fix: prepend each task with an explicit instruction naming the real tools and forbidding the hallucinated ones.

| Task | Baseline | Retrieval |
|---|---|---|
| employees_combined | 100% | 100% |
| currency_simple | 100% | 100% |
| population_single | 100% | 100% |
| two_tools | 20% | 20% |
| no_tool | 60% | 100% |
| **AVERAGE** | **76%** | **84%** |

## What I learned

1. **The bottleneck was not retrieval — it was prompt-example leakage.** A weak model imitates the tools it sees in its prompt examples over the tools it actually has. Naming and forbidding the fake tools fixed the search-flavored tasks (population: 0% → 100%).
2. **Retrieval helps, but only once the leak is controlled.** Unsteered, retrieval lost (40% vs 52%). Steered, retrieval won (84% vs 76%) — fewer, cleaner options compound with clear instructions.
3. **A fix can cause a regression.** Steering the baseline *dropped* `no_tool` from 100% to 60% — over-instruction pushed the model toward tools for a task that needed none. Retrieval avoided this by correctly handing over zero tools.
4. **Two bottlenecks, not one.** `two_tools` stayed at 20% regardless — that failure is multi-step *composition*, a capability limit of the 3B, not tool hallucination. Different problem, different cure.
5. **Non-determinism is fundamental.** Identical runs give different answers; single runs are meaningless. pass@k exists for this reason.

## Limitations (honest)

- **Small sample:** 5 tasks, 5 runs each. Numbers are consistent but noisy; "100%" means 5/5, not "always." Larger runs (n=20+) are needed to confirm.
- **Steering is blunt:** it names specific fake tools to forbid. A cleaner fix would customize smolagents' actual system prompt.
- **CPU-only, one small model:** absolute scores are low by design; the finding is about *deltas* between conditions, not headline accuracy.

## Stack

`smolagents` · `Ollama` (`qwen2.5:3b`) · `sentence-transformers` (`all-MiniLM-L6-v2`) · `uv` · Python 3.11

## Running it

```bash
uv sync
# ensure Ollama is running and the model is pulled:
ollama pull qwen2.5:3b
uv run benchmark.py
```

## Roadmap

- [ ] Scale to n=20 runs for statistical confidence
- [ ] LLM-as-router as a third retrieval strategy (compare vs embeddings)
- [ ] Attack the `two_tools` composition bottleneck
- [ ] Clean prompt customization instead of task-string steering
- [ ] Dockerize for reproducibility