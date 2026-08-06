from smolagents import CodeAgent, OpenAIServerModel
from retriever import retrieve
from tools import TOOL_REGISTRY        # single source of truth (don't redefine tools here)
from steering import steer             # shared steering

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
    from skill_agent import build_agent_for_task
    from benchmark import is_correct

    task = "How many employees do Acme and Initech have combined?"
    expected = 1287

    for attempt in range(5):
        agent, steered_task = build_agent_for_task(task)   # unpack the tuple
        answer = agent.run(steered_task)                    # run the STEERED task
        code = extract_verified_code(agent, answer, expected)
        print(f"\nAttempt {attempt+1}: answer={answer!r} -> {'VERIFIED' if code else 'rejected'}")
        if code:
            print("--- EXTRACTED (VERIFIED) CODE ---")
            print(code)
            break
    else:
        print("\nNo verified success in 5 attempts.")