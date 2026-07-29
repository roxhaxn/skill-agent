from smolagents import CodeAgent, OpenAIServerModel, tool

# --- Model setup (unchanged) ---
model = OpenAIServerModel(
    model_id="qwen2.5:3b",
    api_base="http://localhost:11434/v1",
    api_key="ollama",
)

# --- Our tool (unchanged) ---
@tool
def get_employee_count(company: str) -> int:
    """Returns the number of employees at a given company.

    Args:
        company: The name of the company to look up.
    """
    fake_db = {"acme": 1200, "globex": 34000, "initech": 87}
    return fake_db.get(company.lower(), -1)


# --- Agent factory: builds a FRESH agent every time it's called ---
def build_agent() -> CodeAgent:
    return CodeAgent(
        tools=[get_employee_count],
        model=model,
        add_base_tools=False,
        max_steps=4,
    )


# --- Scoring ---
def normalize(value) -> str:
    """Turn any answer into a comparable, cleaned string."""
    text = str(value).strip().lower()
    try:
        return str(float(text))   # numbers: 1287 == "1287" == "1287.0"
    except ValueError:
        return text               # text: just clean it


def is_correct(agent_answer, expected_answer) -> bool:
    """True if the agent's answer matches the expected one."""
    return normalize(agent_answer) == normalize(expected_answer)


# --- Evaluation (pass@k) ---
def evaluate(build_agent_fn, task: str, expected, n_runs: int = 5) -> float:
    """Run the agent n_runs times on one task; return the success rate (0.0-1.0)."""
    successes = 0
    for i in range(n_runs):
        agent = build_agent_fn()          # fresh agent -> no state leaks
        answer = agent.run(task)
        correct = is_correct(answer, expected)
        if correct:
            successes += 1
        print(f"Run {i+1}: answer={answer!r} correct={correct}")
    return successes / n_runs


# --- Run it ---
if __name__ == "__main__":
    task = "How many employees do Acme and Initech have combined?"
    rate = evaluate(build_agent, task, expected=1287, n_runs=5)
    print(f"\nSuccess rate: {rate:.0%}")