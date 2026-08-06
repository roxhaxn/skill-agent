from benchmark import is_correct


def extract_verified_code(agent, answer, expected):
    """Extract the agent code ONLY if the run produced the correct answer.
    Ran-without-error is NOT enough: a run can succeed technically but
    hallucinate a wrong answer. We gate on correctness."""
    if not is_correct(answer, expected):
        return None

    code_pieces = []
    for step in agent.memory.steps:
        code = getattr(step, "code_action", None)
        error = getattr(step, "error", None)
        if code and error is None:
            code_pieces.append(code.strip())

    return "\n\n".join(code_pieces) if code_pieces else None


if __name__ == "__main__":
    from skill_agent import build_agent_for_task

    task = "How many employees do Acme and Initech have combined?"
    expected = 1287

    for attempt in range(5):
        agent, steered_task = build_agent_for_task(task)
        answer = agent.run(steered_task)
        code = extract_verified_code(agent, answer, expected)
        status = "VERIFIED" if code else "rejected"
        print(f"\nAttempt {attempt+1}: answer={answer!r} -> {status}")
        if code:
            print("--- EXTRACTED (VERIFIED) CODE ---")
            print(code)
            break
    else:
        print("\nNo verified success in 5 attempts.")
