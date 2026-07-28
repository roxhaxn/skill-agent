from smolagents import CodeAgent, OpenAIServerModel

model = OpenAIServerModel(
    model_id="qwen2.5:7b",              # must match `ollama list` exactly
    api_base="http://localhost:11434/v1",  # Ollama's OpenAI-compatible endpoint
    api_key="ollama",                    # dummy value; Ollama ignores it
)

agent = CodeAgent(tools=[], model=model, add_base_tools=True)
result = agent.run("What is 15% of 3400, and what is that number's square root?")
print(result)