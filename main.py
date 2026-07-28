from smolagents import CodeAgent, OpenAIServerModel, tool

model = OpenAIServerModel(
    model_id="qwen2.5:3b",
    api_base="http://localhost:11434/v1",
    api_key="ollama",
)

@tool
def get_employee_count(company: str) -> int:
    """Returns the number of employees at a given company.

    Args:
        company: The name of the company to look up.
    """
    fake_db = {"acme": 1200, "globex": 34000, "initech": 87}
    return fake_db.get(company.lower(), -1)

agent = CodeAgent(tools=[get_employee_count], model=model, add_base_tools=False)
result = agent.run("How many employees do Acme and Initech have combined?")
print(result)
