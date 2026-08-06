from smolagents import CodeAgent, OpenAIServerModel
from retriever import retrieve
from tools import TOOL_REGISTRY
from steering import steer

model = OpenAIServerModel(
    model_id="qwen2.5:3b",
    api_base="http://localhost:11434/v1",
    api_key="ollama",
)


def build_agent_for_task(task: str, threshold: float = 0.3):
    """Retrieve relevant skills for THIS task, build an agent with only those tools,
    and return (agent, steered_task) so callers run the steered version."""
    chosen_tools, chosen_names = [], []
    for skill, score in retrieve(task, k=3):
        if score >= threshold and skill["name"] in TOOL_REGISTRY:
            chosen_tools.append(TOOL_REGISTRY[skill["name"]])
            chosen_names.append(skill["name"])

    agent = CodeAgent(
        tools=chosen_tools,
        model=model,
        add_base_tools=False,
        max_steps=4,
    )
    return agent, steer(task, chosen_names)


if __name__ == "__main__":
    task = "How many employees do Acme and Initech have combined?"
    agent, steered_task = build_agent_for_task(task)
    answer = agent.run(steered_task)
    print("FINAL:", answer)
