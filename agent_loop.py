from skill_agent import build_agent_for_task, model
from skill_extractor import extract_verified_code
from distiller import distill_skill
from skill_library import load_library, save_skill, materialize_skill
from tools import TOOL_REGISTRY


# --- STARTUP: load learned skills from disk into the live registry ---
def bootstrap_learned_skills():
    """Load every persisted skill and register it so it's callable this run."""
    library = load_library()
    for name, record in library.items():
        try:
            fn = materialize_skill(record, TOOL_REGISTRY)
            TOOL_REGISTRY[name] = fn          # now callable by the agent
            print(f"   [bootstrap] loaded learned skill '{name}'")
        except Exception as e:
            print(f"   [bootstrap] skipped '{name}': {e}")
    return library


def already_learned_for_tool(library: dict, tool_name: str) -> bool:
    """Have we already distilled a skill built on this tool?"""
    return any(rec.get("tool") == tool_name for rec in library.values())


def which_tool_was_used(agent) -> str | None:
    """Inspect the successful run to see which known tool the agent actually called."""
    for step in agent.memory.steps:
        code = getattr(step, "code_action", None) or ""
        for tool_name in TOOL_REGISTRY:
            if tool_name + "(" in code:
                return tool_name
    return None


# --- THE LOOP: solve, verify, and learn if it's something new ---
def run_and_learn(task: str, expected, max_attempts: int = 5):
    library = load_library()

    for attempt in range(max_attempts):
        agent, steered_task = build_agent_for_task(task)
        answer = agent.run(steered_task)
        verified_code = extract_verified_code(agent, answer, expected)

        if not verified_code:
            print(f"   attempt {attempt+1}: not verified, retrying")
            continue

        print(f"   attempt {attempt+1}: VERIFIED (answer={answer!r})")

        # We have a correct run. Should we learn a new skill from it?
        tool_used = which_tool_was_used(agent)
        if tool_used is None:
            print("   [learn] no known tool used (pure reasoning) — nothing to distill")
            return answer

        if already_learned_for_tool(library, tool_used):
            print(f"   [learn] already have a skill for '{tool_used}' — skipping")
            return answer

        # New capability! Distill and persist it.
        print(f"   [learn] new capability using '{tool_used}' — distilling")
        skill_code = distill_skill(
            verified_code,
            tool_name=tool_used,
            test_input=["Acme", "Initech"] if tool_used == "get_employee_count" else None,
            expected=expected,
        )
        if skill_code:
            save_skill(
                name=f"learned_{tool_used}",
                description=f"Reusable skill built from a verified run using {tool_used}.",
                code=skill_code,
                tool=tool_used,
            )
        return answer

    print("   no verified success — learned nothing")
    return None


if __name__ == "__main__":
    print("=== BOOTSTRAP: load any previously-learned skills ===")
    bootstrap_learned_skills()

    print("\n=== RUN 1: solve a task and learn from it ===")
    run_and_learn("How many employees do Acme and Initech have combined?", expected=1287)

    print("\n=== Library after run ===")
    print(list(load_library().keys()))