import re
from benchmark import model          # reuse the same Ollama model
from tools import TOOL_REGISTRY


# --- Helper: get a plain-callable version of a @tool ---
def _plain(tool_obj):
    """Return a plain callable for a smolagents @tool (or the object if already callable)."""
    # smolagents Tool objects store the original function; fall back to calling directly.
    fn = getattr(tool_obj, "forward", None) or getattr(tool_obj, "func", None) or tool_obj
    return fn


# --- Piece 1: ask the LLM to generalize the verified code ---
def llm_distill(verified_code: str, tool_name: str) -> str | None:
    """Ask the model to rewrite specific verified code as a general, parameterized function."""
    prompt = (
        "You are refactoring working Python into a reusable function.\n"
        f"The code below solves a task using the tool `{tool_name}`:\n\n"
        f"{verified_code}\n\n"
        "Rewrite it as ONE general function named `learned_skill` that takes a list "
        f"of inputs, calls `{tool_name}` on each, and returns the SUM as an int. "
        "Do NOT call final_answer. Do NOT include print statements. "
        "Return ONLY the function definition in a Python code block, nothing else."
    )
    resp = model([{"role": "user", "content": prompt}])
    text = resp.content if hasattr(resp, "content") else str(resp)

    # Pull the code out of a ```python ... ``` block if present.
    match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


# --- Piece 2: verify a candidate skill by EXECUTING it on a known input ---
def verify_skill(skill_code: str, tool_name: str, test_input, expected) -> bool:
    """Run the candidate skill in a controlled namespace; return True if it gives the right answer."""
    tool_fn = _plain(TOOL_REGISTRY[tool_name])
    namespace = {tool_name: tool_fn}      # make the real tool available to the skill

    try:
        exec(skill_code, namespace)        # define the function
        skill = namespace.get("learned_skill")
        if skill is None:
            return False
        result = skill(test_input)         # actually run it
        return str(result).strip() == str(expected).strip()
    except Exception as e:
        print(f"   [verify] skill failed to execute: {e}")
        return False


# --- Piece 3: deterministic template fallback ---
def template_distill(tool_name: str) -> str:
    """A guaranteed-correct generalization for the 'call tool over a list, sum results' pattern."""
    return (
        f"def learned_skill(items):\n"
        f"    total = 0\n"
        f"    for item in items:\n"
        f"        total += {tool_name}(item)\n"
        f"    return total\n"
    )


# --- Orchestrator: LLM first, template fallback, never store unverified ---
def distill_skill(verified_code: str, tool_name: str, test_input, expected):
    """Return a verified reusable skill (code string), or None if nothing verifies."""
    # Try the LLM.
    candidate = llm_distill(verified_code, tool_name)
    print("\n--- LLM CANDIDATE ---\n" + (candidate or "(none)"))
    if candidate and verify_skill(candidate, tool_name, test_input, expected):
        print("   [distill] LLM skill VERIFIED")
        return candidate

    # Fall back to the template.
    print("   [distill] LLM skill failed; trying template fallback")
    fallback = template_distill(tool_name)
    if verify_skill(fallback, tool_name, test_input, expected):
        print("   [distill] template skill VERIFIED")
        return fallback

    print("   [distill] nothing verified; storing nothing")
    return None


if __name__ == "__main__":
    # The verified code your extractor produced:
    verified_code = (
        "acme_employees = get_employee_count('Acme')\n"
        "initech_employees = get_employee_count('Initech')\n"
        "total_employees = acme_employees + initech_employees\n"
    )

    skill = distill_skill(
        verified_code,
        tool_name="get_employee_count",
        test_input=["Acme", "Initech"],   # known input
        expected=1287,                     # known correct answer
    )

    print("\n=== FINAL DISTILLED SKILL ===")
    print(skill if skill else "(distillation failed)")