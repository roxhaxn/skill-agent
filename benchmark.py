from smolagents import CodeAgent, OpenAIServerModel
from retriever import retrieve
from tools import TOOL_REGISTRY
from tasks import TASKS

model = OpenAIServerModel(
    model_id="qwen2.5:3b",
    api_base="http://localhost:11434/v1",
    api_key="ollama",
)

ALL_TOOLS = list(TOOL_REGISTRY.values())   # every tool, for the baseline


def normalize(value) -> str:
    text = str(value).strip().lower()
    try:
        return str(float(text))
    except ValueError:
        return text


def is_correct(agent_answer, expected) -> bool:
    return normalize(agent_answer) == normalize(expected)


def build_baseline_agent(task: str) -> CodeAgent:
    """Baseline: hand the agent ALL tools, no retrieval."""
    return CodeAgent(tools=ALL_TOOLS, model=model, add_base_tools=False, max_steps=4)


def build_retrieval_agent(task: str, threshold: float = 0.3) -> CodeAgent:
    """Retrieval: hand the agent only the skills relevant to THIS task."""
    chosen = []
    for skill, score in retrieve(task, k=3):
        if score >= threshold and skill["name"] in TOOL_REGISTRY:
            chosen.append(TOOL_REGISTRY[skill["name"]])
    return CodeAgent(tools=chosen, model=model, add_base_tools=False, max_steps=4)


def run_condition(build_fn, n_runs: int = 5) -> dict:
    """Run every task n_runs times with the given agent-builder; return per-task success rates."""
    results = {}
    for t in TASKS:
        successes = 0
        for _ in range(n_runs):
            agent = build_fn(t["task"])
            answer = agent.run(t["task"])
            if is_correct(answer, t["expected"]):
                successes += 1
        results[t["id"]] = successes / n_runs
    return results


if __name__ == "__main__":
    N = 5
    print(f"Running benchmark ({N} runs per task per condition)... this will take a while.\n")

    baseline = run_condition(build_baseline_agent, n_runs=N)
    retrieval = run_condition(build_retrieval_agent, n_runs=N)

    # --- Results table ---
    print(f"\n{'Task':<22}{'Baseline':>10}{'Retrieval':>11}")
    print("-" * 43)
    for t in TASKS:
        b = baseline[t["id"]]
        r = retrieval[t["id"]]
        print(f"{t['id']:<22}{b:>9.0%}{r:>10.0%}")
    print("-" * 43)
    avg_b = sum(baseline.values()) / len(TASKS)
    avg_r = sum(retrieval.values()) / len(TASKS)
    print(f"{'AVERAGE':<22}{avg_b:>9.0%}{avg_r:>10.0%}")