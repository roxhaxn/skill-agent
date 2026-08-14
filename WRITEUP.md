# When "smarter" retrieval made my agent worse: debugging a tool-hallucination bug

I built a small LLM agent that picks tools for a task using embedding-based retrieval — the idea being that if you only hand the model the tools it actually needs, it should do better than an agent drowning in every tool at once. That hypothesis was wrong, in an interesting way. Here's how I found out, and what was really going on.

## Setup

I developed this on a CPU-only machine, so I ran a small local model — `qwen2.5:3b` via Ollama — rather than something bigger. This wasn't just a limitation to apologize for: the 7B model took about 122 seconds *per step*, which made a benchmark of hundreds of runs impractical. And it turned out the small model was an advantage. A weaker model fails more often and more visibly, which made the failure mode below far easier to catch than a robust model would have — the small model was effectively a stress test.

The setup: a `CodeAgent` (it writes and runs Python to call tools), an embedding retriever (`sentence-transformers`, cosine similarity over tool descriptions), and a pass@k benchmark that runs each task many times and reports a success *rate*, because the model is non-deterministic.

## The surprise

I expected retrieval — handing the agent only the relevant tools — to beat a baseline that gets every tool. It did the opposite.

- Baseline (all tools): **52%**
- Retrieval (only relevant tools): **40%**

Retrieval made the agent *worse*. That was the exact opposite of my hypothesis, so I had to figure out why.

## The false lead

My first suspicion: my retriever used a similarity threshold to decide which tools to include, and maybe it was too aggressive — cutting off the needed tool, so the agent got handed *nothing* and had no choice but to flail.

So I tested it directly. I ran the retriever on the task that failed hardest ("What is the population of Tokyo?") and looked at the scores. The correct tool, `get_city_population`, scored **0.54** — well above my threshold, and far ahead of everything else. The tool *was* being offered to the agent.

That killed the threshold theory. The retriever was working fine. The problem was somewhere else.

## The real cause

I went back to the raw run logs and looked at what the agent was *actually doing*. The pattern jumped out: over and over, the agent was calling tools like `wikipedia_search` and `web_search` — tools that **don't exist in my project**. It was ignoring the real, relevant tool it had been handed and reaching for imaginary ones.

Where were those imaginary tools coming from? The agent framework's *own system prompt*. The default prompt includes example tasks that demonstrate tools like `wikipedia_search` and `web_search`. A small model can't reliably tell "example tool from the instructions" apart from "tool I actually have" — so it imitated the examples instead of using its real tools.

That's why retrieval looked like it hurt. It wasn't retrieval's fault at all — the agent was being pulled toward hallucinated tools by prompt contamination, and retrieval just happened to expose it on certain tasks.

## The fix

Once I understood the cause, the fix was direct: steer the model explicitly. Before each task, I prepend an instruction that names the real tools available and forbids the hallucinated ones ("you have ONLY these tools; do not call web_search or wikipedia_search — they will fail").

The results (20 runs per task):

| Condition | Before steering | After steering |
|---|---|---|
| Baseline (all tools) | 52% | **81%** |
| Retrieval (relevant tools) | 40% | **88%** |

Two things happened. Both conditions jumped. And retrieval, which had *lost* to the baseline before, now *beat* it — because once the hallucination was controlled, giving the agent fewer, cleaner options actually helped, most of all on the hardest multi-step task.

## What I took away

- The bug wasn't in the component I first blamed. I assumed "retrieval is broken"; the retriever was fine, and the real issue was the model imitating its own prompt's examples. Checking my first theory directly — instead of acting on it — is what saved me.
- A wrong-but-confident answer is more dangerous than a crash. None of the failing runs errored; they returned plausible wrong numbers. That's why I score every run against a known answer rather than trusting it ran.
- The weak model was a feature. A stronger model might have used the right tool anyway and hidden the bug entirely. The 3B's fragility is what made the failure legible.

## Honest limits

All numbers are on a 3B model on CPU, across a small benchmark (n=20 per task). Absolute accuracy is low by design — the finding is about the *deltas* between conditions, not headline scores. Broader task variety is the obvious next step.

---

*Code: [[github.com/roxhaxn/skill-agent]]*