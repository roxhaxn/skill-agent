from sentence_transformers import SentenceTransformer, util

# 1. Load the embedding model ONCE. Small, fast, CPU-friendly, outputs 384 numbers.
print("Loading embedding model (first run downloads ~80MB)...")
embedder = SentenceTransformer("all-MiniLM-L6-v2")

# 2. Our skill library. For now, each skill is just a name + a description.
#    (Later, each will also carry its actual tool function.)
SKILLS = [
    {"name": "get_employee_count", "description": "Look up the number of employees (headcount, workforce size) at a company."},
    {"name": "convert_currency",   "description": "Convert an amount of money from one currency to another using exchange rates."},
    {"name": "get_weather",        "description": "Get the current weather or temperature for a city or location."},
    {"name": "bake_bread",         "description": "Step-by-step recipe and instructions for baking bread at home."},
    {"name": "calculate_distance", "description": "Compute the distance between two cities or geographic points."},
]

# 3. BUILD TIME: embed every skill description once, up front.
skill_descriptions = [s["description"] for s in SKILLS]
skill_vectors = embedder.encode(skill_descriptions, convert_to_tensor=True)


def retrieve(task: str, k: int = 3):
    """Return the top-k skills most relevant to the task, each with its score."""
    # QUERY TIME: embed the incoming task the SAME way we embedded the skills.
    task_vector = embedder.encode(task, convert_to_tensor=True)

    # COMPARE: cosine similarity between the task and every skill (one score each).
    scores = util.cos_sim(task_vector, skill_vectors)[0]

    # PICK TOP-K: pair each skill with its score, sort high→low, keep k.
    ranked = sorted(zip(SKILLS, scores.tolist()), key=lambda pair: pair[1], reverse=True)
    return ranked[:k]


if __name__ == "__main__":
    tasks = [
        "How many employees do Acme and Initech have combined?",
        "What's the headcount at Google?",
        "How much is 100 dollars in euros?",
        "Is it going to rain in Paris tomorrow?",
    ]
    for task in tasks:
        print(f"\nTask: {task}")
        for skill, score in retrieve(task, k=3):
            print(f"   {score:.2f}  {skill['name']}")