from skill_agent import build_agent_for_task, model
from skill_extractor import extract_verified_code
from distiller import distill_skill
from skill_library import load_library, save_skill, materialize_skill
from tools import TOOL_REGISTRY
from tasks import TASKS


# --- STARTUP: load learned skills from disk into the live registry ---
def bootstrap_learned_skills():
    """Load every persisted skill and register it so it is callable this run."""
    library = load_library()
    for name, record in library.items():
        try:
            fn = materialize_skill(record, TOOL_REGISTRY)
            TOOL_REGISTRY[name] = fn
            print(f"   [bootstrap] loaded learned skill '{name}'")
        except Exception as e:
            print(f"   [bootstrap] skipped '{name}': {e}")
    return library


def already_learned_for_tool(library: dict, tool_name: str) -> bool:
    return any(rec.get("tool") == tool_name for rec in library.values())


def which_tool_was_used(agent) -> str | None:
    for step in agent.memory.steps:
        code = getattr(step, "code_action", None) or ""
        for tool_name in TOOL_REGISTRY:
            if tool_name + "(" in code:
                return tool_name
    return None


# --- THE LOOP: takes a whole task dict (needs its test_case for distillation) ---
def run_and_learn(task_dict: dict, max_attempts: int = 5):
    task = task_dict["task"]
    expected = task_dict["expected"]
    test_case = task_dict.get("test_case")

    library = load_library()

    for attempt in range(max_attempts):
        agent, steered_task = build_agent_for_task(task)
        answer = agent.run(steered_task)
        verified_code = extract_verified_code(agent, answer, expected)

        if not verified_code:
            print(f"   attempt {attempt+1}: not verified, retrying")
            continue

        print(f"   attempt {attempt+1}: VERIFIED (answer={answer!r})")

        tool_used = which_tool_was_used(agent)
        if tool_used is None:
            print("   [learn] no known tool used (pure reasoning) - nothing to distill")
            return answer

        if already_learned_for_tool(library, tool_used):
            print(f"   [learn] already have a skill for '{tool_used}' - skipping")
            return answer

        print(f"   [learn] new capability using '{tool_used}' - distilling")
        skill_code = distill_skill(verified_code, tool_used, test_case)
        if skill_code:
            save_skill(
                name=f"learned_{tool_used}",
                description=f"Reusable skill built from a verified run using {tool_used}.",
                code=skill_code,
                tool=tool_used,
            )
        return answer

    print("   no verified success - learned nothing")
    return None


def get_task(task_id: str) -> dict:
    for t in TASKS:
        if t["id"] == task_id:
            return t
    raise ValueError(f"no task with id {task_id}")


if __name__ == "__main__":
    print("=== BOOTSTRAP: load any previously-learned skills ===")
    bootstrap_learned_skills()

    print("\n=== RUN 1: employees (already learned -> should skip) ===")
    run_and_learn(get_task("employees_combined"))

    print("\n=== RUN 2: currency (new capability -> should learn) ===")
    run_and_learn(get_task("currency_simple"))

    print("\n=== Library after runs ===")
    print(list(load_library().keys()))
