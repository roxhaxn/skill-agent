import re
from benchmark import model
from tools import TOOL_REGISTRY


def _plain(tool_obj):
    return getattr(tool_obj, "forward", None) or getattr(tool_obj, "func", None) or tool_obj


# --- Pattern templates: two general shapes a learned skill can take ---
def template_map_reduce(tool_name: str) -> str:
    """Call one tool over a list of items and sum the results."""
    return (
        "def learned_skill(items):\n"
        "    total = 0\n"
        "    for item in items:\n"
        f"        total += {tool_name}(item)\n"
        "    return total\n"
    )


def template_single_call(tool_name: str) -> str:
    """Make one parameterized tool call and return its result."""
    return (
        "def learned_skill(kwargs):\n"
        f"    return {tool_name}(**kwargs)\n"
    )


TEMPLATES = {
    "map_reduce": template_map_reduce,
    "single_call": template_single_call,
}


# --- Verify a candidate skill by EXECUTING it on the task's known test case ---
def verify_skill(skill_code: str, tool_name: str, test_input, expected) -> bool:
    tool_fn = _plain(TOOL_REGISTRY[tool_name])
    namespace = {tool_name: tool_fn}
    try:
        exec(skill_code, namespace)
        skill = namespace.get("learned_skill")
        if skill is None:
            return False
        result = skill(test_input)
        return str(result).strip() == str(expected).strip()
    except Exception as e:
        print(f"   [verify] failed: {e}")
        return False


# --- LLM distillation (tries to generalize the verified code) ---
def llm_distill(verified_code: str, tool_name: str, pattern: str) -> str | None:
    shape = ("a function learned_skill(items) that calls the tool on each item in a list and sums results"
             if pattern == "map_reduce"
             else "a function learned_skill(kwargs) that calls the tool once with **kwargs and returns the result")
    prompt = (
        f"Refactor this working code into {shape}, using the tool `{tool_name}`:\n\n"
        f"{verified_code}\n\n"
        "Return ONLY the function definition in a Python code block. No prints, no final_answer."
    )
    resp = model([{"role": "user", "content": prompt}])
    text = resp.content if hasattr(resp, "content") else str(resp)
    match = re.search(r"```(?:python)?\s*(.*?)```", text, re.DOTALL)
    return match.group(1).strip() if match else text.strip()


# --- Orchestrator: try LLM then template, for the task's pattern; keep what verifies ---
def distill_skill(verified_code: str, tool_name: str, test_case: dict):
    if not test_case:
        print("   [distill] no test_case (no tool) - nothing to distill")
        return None

    pattern = test_case["pattern"]
    test_input = test_case["input"]
    expected = test_case["expected"]

    # 1. Try the LLM for this pattern.
    candidate = llm_distill(verified_code, tool_name, pattern)
    print(f"\n--- LLM CANDIDATE ({pattern}) ---\n{candidate}")
    if candidate and verify_skill(candidate, tool_name, test_input, expected):
        print("   [distill] LLM skill VERIFIED")
        return candidate

    # 2. Fall back to the template for this pattern.
    print("   [distill] LLM failed; trying template")
    fallback = TEMPLATES[pattern](tool_name)
    if verify_skill(fallback, tool_name, test_input, expected):
        print("   [distill] template skill VERIFIED")
        return fallback

    print("   [distill] nothing verified; storing nothing")
    return None
