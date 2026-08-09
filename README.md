# skill-agent

A **self-improving LLM agent** that solves tasks, verifies its own answers, and distills successful runs into reusable skills — growing a persistent skill library with no human in the loop. Built from scratch on [smolagents](https://github.com/huggingface/smolagents), running fully offline on a CPU-only machine.

The project began as an investigation ("does retrieval-based tool selection make a small agent more reliable?") and grew into a working self-improving loop. Throughout, the emphasis is on **measurement and verification**: every claim is benchmarked, and the agent only learns from runs it can prove are correct.

## What it does

```
startup:  load learned skills from disk -> register them as callable tools
   task:  retrieve relevant tools -> build a steered agent -> run
 verify:  is the answer correct vs ground truth?  --no--> discard
   learn: new capability?  --yes--> distill into a reusable skill
                                     -> verify the skill by EXECUTING it
                                     -> persist to the library
  reuse:  future tasks retrieve and call learned skills
```

The library only ever grows with **execution-verified** skills — the agent cannot poison itself with hallucinated or broken code.

## Key results

Retrieval + prompt-steering benchmark, **20 runs per task** (`qwen2.5:3b` via Ollama):

| Condition | Avg success |
|---|---|
| Baseline (all tools, no steering) | 52% |
| Retrieval only (no steering) | 40% — *retrieval hurt* |
| Baseline + steering | 81% |
| **Retrieval + steering** | **88%** |

Headline finding: **retrieval alone made the agent worse**, until the root cause — the model hallucinating tools leaked from the system prompt's examples — was diagnosed and fixed. Once fixed, focused retrieval *beat* the all-tools baseline, with the largest gain on the hardest multi-step task (25% -> 50%).

## The self-improving loop

The agent learns reusable skills from its own verified successes, across two general patterns:

- **map_reduce** — call one tool over a list and aggregate (e.g. summing employee counts across companies)
- **single_call** — one parameterized tool call (e.g. currency conversion)

Distillation is attempted by the LLM first, with a deterministic template fallback; whichever candidate passes **execution-based verification** is kept. Learned skills are persisted to `skill_library.json` and reloaded on startup.

Demonstrated end to end: the agent solves an employee-count task, distills a `map_reduce` skill, and reuses it on company combinations it was never asked about (e.g. Acme+Globex). Given a currency task, it recognizes a *new* capability and learns a `single_call` skill — growing the library to two skills with no human intervention. It correctly **skips** re-learning known capabilities and **refuses** to store skills that fail verification.

## Method

- **Model:** `qwen2.5:3b` served locally by Ollama, via smolagents' `OpenAIServerModel`. CPU-only.
- **Tools:** deterministic tools with fixed fake data (`get_employee_count`, `convert_currency`, `get_city_population`) so every task has a known, verifiable answer.
- **Retrieval:** tool descriptions embedded with `sentence-transformers` (`all-MiniLM-L6-v2`); tasks matched by cosine similarity.
- **Scoring:** exact-match after normalization; never eyeballed.
- **pass@k:** each task run 20 times; success *rate* reported, because the model is non-deterministic.
- **Steering:** each task is prefixed with an instruction naming the real tools and forbidding the hallucinated ones.

## What I learned

1. **The bottleneck was prompt-example leakage, not retrieval.** A weak model imitates the tools in its prompt examples over the tools it actually has. Steering fixed the search-flavored tasks (population: 0% -> 95%).
2. **Retrieval helps only once the leak is controlled.** Unsteered it lost (40% vs 52%); steered it won (88% vs 81%).
3. **Focused tools help most on hard tasks** — the multi-step task saw the biggest gain (25% -> 50%).
4. **Never learn from unverified output.** Execution-based verification gates both skill extraction and distillation, so the agent cannot amplify its own hallucinations into the library — demonstrated when a mismatched distillation was correctly rejected.
5. **Sample size matters.** At n=5 several tasks read 100% and a regression appeared that vanished at n=20 — it was noise. pass@k with adequate n is essential.

## Limitations (honest)

- **Distillation covers two patterns** (map_reduce, single_call). Extending the pattern set, or moving toward open-ended synthesis, is future work.
- **Task breadth:** 5 benchmark tasks; run count is solid (n=20) but more varied tasks are the next credibility step.
- **`exec` of stored skills:** learned skills are executed to verify and reload them. This is kept safe by only ever storing verified skills; hardening the execution boundary (sandboxing) is on the roadmap.
- **CPU-only, one small model:** absolute scores are modest by design — the findings are about *deltas* between conditions.

## Stack

`smolagents` · `Ollama` (`qwen2.5:3b`) · `sentence-transformers` (`all-MiniLM-L6-v2`) · `uv` · Python 3.11

## Layout

| File | Role |
|---|---|
| `tools.py` | deterministic tools + registry |
| `retriever.py` | embedding-based tool retrieval |
| `steering.py` | shared prompt-steering |
| `benchmark.py` | pass@k benchmark, baseline vs retrieval |
| `skill_extractor.py` | extract verified code from a successful run |
| `distiller.py` | distill verified code into a reusable skill (2 patterns) |
| `skill_library.py` | JSON persistence: save / load / materialize skills |
| `agent_loop.py` | the autonomous self-improving loop |

## Running it

```bash
uv sync
ollama pull qwen2.5:3b        # ensure Ollama is running
uv run benchmark.py           # reproduce the benchmark
uv run agent_loop.py          # watch the agent learn + reuse skills
```

## Roadmap

- [ ] LLM-as-router as a third retrieval strategy (vs embeddings)
- [ ] More distillation patterns / broader task set
- [ ] Sandbox skill execution (Docker)
- [ ] Hugging Face Space demo