# Each task has: the question, the expected answer, and why it's here.
# Expected answers are computed from the KNOWN fake data in tools.py.

TASKS = [
    {
        "id": "employees_combined",
        "task": "How many employees do Acme and Initech have combined?",
        "expected": 1287,                      # 1200 + 87
        "note": "single tool, two lookups + addition",
    },
    {
        "id": "currency_simple",
        "task": "How much is 100 USD in EUR?",
        "expected": 90.0,                      # 100 * 0.90
        "note": "different tool - tests retriever picking the right one",
    },
    {
        "id": "population_single",
        "task": "What is the population of Tokyo?",
        "expected": 14_000_000,
        "note": "single lookup, no arithmetic",
    },
    {
        "id": "two_tools",
        "task": "What is the combined population of Paris and Delhi, converted to millions?",
        "expected": 34.1,                      # (2.1M + 32M) / 1M
        "note": "harder: two lookups + arithmetic",
    },
    {
        "id": "no_tool",
        "task": "What is 25 multiplied by 4?",
        "expected": 100,
        "note": "no tool needed - tests over-reaching",
    },
]