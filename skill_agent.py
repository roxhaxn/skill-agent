from smolagents import CodeAgent, OpenAIServerModel, tool
from retriever import retrieve   # reuse what you already built

model = OpenAIServerModel(
    model_id="qwen2.5:3b",
    api_base="http://localhost:11434/v1",
    api_key="ollama",
)

# --- The ACTUAL tool implementations, keyed by name ---
# The retriever returns skill *descriptions*; here's where the real code lives.
@tool
def get_employee_count(company: str) -> int:
    """Returns the number of employees at a given company.

    Args:
        company: The name of the company to look up.
    """
    fake_db = {"acme": 1200, "globex": 34000, "initech": 87}
    return fake_db.get(company.lower(), -1)

# A registry mapping skill name -> real function
TOOL_REGISTRY = {
    "get_employee_count": get_employee_count,
    # (others will be added as you build them)
}


def build_agent_for_task(task: str, threshold: float = 0.3) -> CodeAgent:
    """Retrieve relevant skills for THIS task and build an agent with only those tools."""
    retrieved = retrieve(task, k=3)

    chosen_tools = []
    for skill, score in retrieved:
        if score >= threshold and skill["name"] in TOOL_REGISTRY:
            chosen_tools.append(TOOL_REGISTRY[skill["name"]])
            print(f"   [retriever] included {skill['name']} (score {score:.2f})")

    return CodeAgent(
        tools=chosen_tools,
        model=model,
        add_base_tools=False,
        max_steps=4,
    )


if __name__ == "__main__":
    from main import evaluate   # reuse your pass@k harness

    task = "How many employees do Acme and Initech have combined?"

    # Wrap build_agent_for_task so evaluate() can call it with no arguments,
    # the same way it called build_agent before.
    def build():
        return build_agent_for_task(task)

    rate = evaluate(build, task, expected=1287, n_runs=5)
    print(f"\nRetrieval agent success rate: {rate:.0%}")
    print("(Baseline was 40%)")