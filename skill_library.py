import json
import os

LIBRARY_PATH = "skill_library.json"


def load_library() -> dict:
    """Load all persisted skills from disk. Returns {} if the library doesn't exist yet."""
    if not os.path.exists(LIBRARY_PATH):
        return {}
    with open(LIBRARY_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_skill(name: str, description: str, code: str, tool: str) -> None:
    """Add one verified skill to the library and write it back to disk."""
    library = load_library()
    library[name] = {
        "description": description,
        "code": code,
        "tool": tool,
    }
    with open(LIBRARY_PATH, "w", encoding="utf-8") as f:
        json.dump(library, f, indent=2)
    print(f"   [library] saved skill '{name}' ({len(library)} total)")


def materialize_skill(record: dict, tool_registry: dict):
    """Turn a stored skill record back into a callable function.

    The skill's code calls a tool by name (e.g. get_employee_count), so we
    exec it in a namespace that contains the real tool function.
    """
    tool_obj = tool_registry[record["tool"]]
    # get a plain-callable version of the @tool (same helper idea as the distiller)
    tool_fn = getattr(tool_obj, "forward", None) or getattr(tool_obj, "func", None) or tool_obj

    namespace = {record["tool"]: tool_fn}
    exec(record["code"], namespace)          # defines 'learned_skill' in namespace
    return namespace["learned_skill"]


if __name__ == "__main__":
    # Demo: save a skill, then load it back and USE it — proving persistence works.
    from tools import TOOL_REGISTRY

    # 1. Save the verified skill the distiller produced.
    save_skill(
        name="sum_employee_counts",
        description="Sum the employee counts across a list of companies.",
        code=(
            "def learned_skill(input_list):\n"
            "    return sum(get_employee_count(x) for x in input_list)\n"
        ),
        tool="get_employee_count",
    )

    # 2. Load the library fresh from disk (simulating a new run).
    library = load_library()
    print(f"\nLibrary now contains: {list(library.keys())}")

    # 3. Materialize the skill and actually run it on a NEW input.
    skill_fn = materialize_skill(library["sum_employee_counts"], TOOL_REGISTRY)
    print("Reused skill on ['Acme', 'Globex']:", skill_fn(["Acme", "Globex"]))
    print("Reused skill on ['Acme', 'Initech']:", skill_fn(["Acme", "Initech"]))