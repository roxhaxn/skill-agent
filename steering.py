def steer(task: str, tool_names: list[str]) -> str:
    """Wrap a task with an explicit instruction to use only the real tools.

    Counteracts smolagents' system-prompt example tools (web_search,
    wikipedia_search) that a small model tends to hallucinate.
    """
    if tool_names:
        tools_str = ", ".join(tool_names)
        instruction = (
            f"IMPORTANT: You have ONLY these tools available: {tools_str}. "
            f"Do NOT call any other function such as web_search, wikipedia_search, "
            f"or requests — they do not exist and will fail. "
            f"If a tool is needed, use only the ones listed. "
        )
    else:
        instruction = (
            "IMPORTANT: You have NO special tools. Solve this using plain Python "
            "computation only. Do NOT call web_search, wikipedia_search, or import "
            "external libraries — they will fail. "
        )
    return instruction + "\n\nTask: " + task