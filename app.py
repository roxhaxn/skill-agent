import gradio as gr
from agent_loop import (
    bootstrap_learned_skills,
    run_and_learn,
    which_tool_was_used,
    already_learned_for_tool,
)
from skill_agent import build_agent_for_task
from skill_extractor import extract_verified_code
from distiller import distill_skill
from skill_library import load_library, save_skill
from tools import TOOL_REGISTRY
from tasks import TASKS

# Load any previously-learned skills once at startup.
bootstrap_learned_skills()


def library_table():
    """Current skill library as rows for display."""
    lib = load_library()
    if not lib:
        return [["(empty)", "", ""]]
    return [[name, rec["tool"], rec["description"]] for name, rec in lib.items()]


def solve_and_learn(task_text, expected_text):
    """Run the real agent on a task, streaming progress to the UI."""
    log = ""

    def emit(line):
        nonlocal log
        log += line + "\n"
        return log

    # Parse expected answer (numbers if possible).
    expected = expected_text.strip()
    try:
        expected = float(expected) if "." in expected else int(expected)
    except ValueError:
        pass

    yield emit(f"Task: {task_text}"), library_table()
    yield emit("Retrieving relevant tools + building steered agent..."), library_table()

    agent, steered_task = build_agent_for_task(task_text)
    yield emit("Running the agent (this can take ~30-60s on CPU)..."), library_table()

    answer = agent.run(steered_task)
    yield emit(f"Agent answered: {answer!r}"), library_table()

    verified = extract_verified_code(agent, answer, expected)
    if not verified:
        yield emit(f"NOT verified against expected={expected!r}. Nothing learned."), library_table()
        return

    yield emit("Answer VERIFIED against ground truth."), library_table()

    tool_used = which_tool_was_used(agent)
    library = load_library()

    if tool_used is None:
        yield emit("Solved by pure reasoning (no tool) - nothing to distill."), library_table()
        return

    if already_learned_for_tool(library, tool_used):
        yield emit(f"Already have a skill for '{tool_used}' - skipping (no duplicate)."), library_table()
        return

    yield emit(f"New capability using '{tool_used}' - distilling a reusable skill..."), library_table()

    # Find the matching task's test_case (needed to verify the distilled skill).
    test_case = None
    for t in TASKS:
        if t["task"].strip().lower() == task_text.strip().lower():
            test_case = t.get("test_case")
            break

    if test_case is None:
        yield emit("No test_case for this task, so the skill can't be verified - not stored.\n"
                   "(Try one of the example tasks below to see learning.)"), library_table()
        return

    skill_code = distill_skill(verified, tool_used, test_case)
    if skill_code:
        save_skill(
            name=f"learned_{tool_used}",
            description=f"Reusable skill built from a verified run using {tool_used}.",
            code=skill_code,
            tool=tool_used,
        )
        yield emit(f"Distilled skill VERIFIED and SAVED. Library grew!"), library_table()
    else:
        yield emit("Distillation failed verification - nothing stored (safety gate working)."), library_table()


# --- UI ---
TASK_CHOICES = {t["task"]: str(t["expected"]) for t in TASKS if t["tool"] is not None}

with gr.Blocks(title="skill-agent") as demo:
    gr.Markdown("# skill-agent — a self-improving LLM agent\n"
                "Pick a task, watch the agent retrieve tools, solve it, verify against ground truth, "
                "and *learn a reusable skill*. Runs on a local `qwen2.5:3b` via Ollama. "
                "Every learned skill is execution-verified before it's stored.")

    with gr.Row():
        with gr.Column():
            task_in = gr.Dropdown(
                label="Task",
                choices=list(TASK_CHOICES.keys()),
                value=list(TASK_CHOICES.keys())[0],
            )
            expected_in = gr.Textbox(label="Expected answer (ground truth)", value=list(TASK_CHOICES.values())[0])
            run_btn = gr.Button("Solve & Learn", variant="primary")
            reset_btn = gr.Button("Reset skill library (for a fresh demo)")
        with gr.Column():
            log_out = gr.Textbox(label="Live progress", lines=14)

    gr.Markdown("### Skill library (grows as the agent learns)")
    lib_out = gr.Dataframe(headers=["skill", "tool", "description"], value=library_table())

    # When a task is picked, auto-fill its expected answer.
    def fill_expected(task):
        return TASK_CHOICES.get(task, "")
    task_in.change(fill_expected, inputs=task_in, outputs=expected_in)

    run_btn.click(solve_and_learn, inputs=[task_in, expected_in], outputs=[log_out, lib_out])

    # Reset lets you demo the library growing from empty.
    def reset_library():
        import os
        if os.path.exists("skill_library.json"):
            os.remove("skill_library.json")
        return library_table()
    reset_btn.click(reset_library, outputs=lib_out)

if __name__ == "__main__":
    demo.launch()