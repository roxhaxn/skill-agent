# skill-agent

A research project investigating whether giving a small local LLM a **retrieved, focused set of tools** — instead of all tools at once — makes it more reliable. Built from scratch on [smolagents](https://github.com/huggingface/smolagents), running fully offline on a CPU-only machine.

The goal was not to build the best agent, but to **measure** how design choices affect a weak model's success rate, and to diagnose *why* it fails.

## TL;DR result

5-task benchmark, **20 runs per task** (`qwen2.5:3b` via Ollama):

| Condition | Avg success |
|---|---|
| Baseline (all tools, no steering) | 52% |
| Retrieval only (no steering) | 40% — *retrieval hurt* |
| Baseline + prompt steering | 81% |
| **Retrieval + prompt steering** | **88%** |

Headline finding: **retrieval alone made the agent worse**, until the real root cause — the model hallucinating tools leaked from the system prompt's examples — was diagnosed and fixed. Once fixed, focused retrieval *beat* the all-tools baseline, with the largest gain on the hardest multi-step task.

## The question

A `CodeAgent` writes Python to call tools. When a small model has many tools, does it get confused? Hypothesis:

> If the agent is handed only the tools relevant to the current task, it will hallucinate less and succeed more often than an agent given every tool at once.

## Method

- **Model:** `qwen2.5:3b` served locally by Ollama, called via smolagents' `OpenAIServerModel`. CPU-only.
- **Tools:** three deterministic tools with fixed fake data (`get_employee_count`, `convert_currency`, `get_city_population`) so every task has a known, verifiable answer.
- **Retrieval:** each tool's description is embedded with `sentence-transformers` (`all-MiniLM-L6-v2`); the task is embedded the same way; tools above a cosine-similarity threshold are handed to the agent.
- **Scoring:** exact-match after normalization (numbers compared as floats), never eyeballed.
- **pass@k:** every task is run 20 times and the **success rate** is reported, because the model is non-deterministic.

## Tasks

| Task | Needs | Tests |
|---|---|---|
| employees_combined | 1 tool, 2 lookups + add | basic tool use |
| currency_simple | 1 tool | picking the right tool |
| population_single | 1 tool | search-flavored temptation |
| two_tools | 2 lookups + arithmetic | multi-step composition |
| no_tool | none (`25 * 4`) | restraint / over-reaching |

## Results

### Before steering (n=5, exploratory)

| Task | Baseline | Retrieval |
|---|---|---|
| employees_combined | 60% | 40% |
| currency_simple | 60% | 40% |
| population_single | 40% | 0% |
| two_tools | 0% | 20% |
| no_tool | 100% | 100% |
| **AVERAGE** | **52%** | **40%** |

Retrieval underperformed. Investigation showed the retriever worked correctly (the population task ranked `get_city_population` at 0.54, well clear of everything else) — the agent was **ignoring** the retrieved tool and hallucinating `web_search` / `wikipedia_search` / `import requests`, all of which appear in smolagents' default system-prompt examples. The most search-flavored task (population) failed hardest.

### After prompt steering (n=20)

Fix: prepend each task with an explicit instruction naming the real tools and forbidding the hallucinated ones.

| Task | Baseline | Retrieval |
|---|---|---|
| employees_combined | 95% | 100% |
| currency_simple | 95% | 95% |
| population_single | 95% | 95% |
| two_tools | 25% | 50% |
| no_tool | 95% | 100% |
| **AVERAGE** | **81%** | **88%** |

## What I learned

1. **The bottleneck was not retrieval — it was prompt-example leakage.** A weak model imitates the tools it sees in its prompt examples over the tools it actually has. Naming and forbidding the fake tools fixed the search-flavored tasks (population: 0% -> 95%).
2. **Retrieval helps, but only once the leak is controlled.** Unsteered, retrieval lost (40% vs 52%). Steered, retrieval won (88% vs 81%) — fewer, cleaner options compound with clear instructions.
3. **Focused tools help most on hard tasks.** The clearest win is `two_tools` (multi-step): retrieval **doubled** baseline (50% vs 25%). When the task is hard, spending the model's limited reasoning on the problem rather than tool selection matters most.
4. **Two bottlenecks, not one.** `two_tools` remains the weakest task even with retrieval — that failure is multi-step *composition*, a capability limit of the 3B, not tool hallucination. Different problem, different cure.
5. **Sample size matters.** At n=5, several tasks showed 100% and `no_tool` appeared to regress to 60% under steering. At n=20 the 100%s settled to ~95% (rare failures the small sample missed) and the `no_tool` "regression" disappeared — it was small-sample noise. This is why pass@k with adequate n is essential.

## Limitations (honest)

- **Task breadth:** 5 tasks. Run count is solid (n=20) but broader task variety is the next credibility frontier.
- **Steering is blunt:** it names specific fake tools to forbid. A cleaner fix would customize smolagents' system prompt directly.
- **CPU-only, one small model:** absolute scores are modest by design; the finding is about *deltas* between conditions, not headline accuracy.

## Stack

`smolagents` · `Ollama` (`qwen2.5:3b`) · `sentence-transformers` (`all-MiniLM-L6-v2`) · `uv` · Python 3.11

## Running it

```bash
uv sync
ollama pull qwen2.5:3b   # ensure Ollama is running
uv run benchmark.py
```

## Roadmap (v2)

- [ ] **Self-improving loop:** agent distills successful runs into reusable skills, stored and retrieved automatically
- [ ] LLM-as-router as a third retrieval strategy (vs embeddings)
- [ ] Broaden to 12+ tasks
- [ ] Attack the `two_tools` composition bottleneck
- [ ] Dockerize + Hugging Face Space demo