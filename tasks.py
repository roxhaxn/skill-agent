# Each task: the question, expected answer, note, and a test_case used to
# VERIFY any skill distilled from a successful run of this task.
#
# test_case.pattern:
#   "map_reduce" -> skill(items) calls one tool over a list and sums
#   "single_call" -> skill(kwargs) makes one parameterized tool call
# test_case.input is what we pass the distilled skill; test_case.expected
# is what it must return to be accepted into the library.

TASKS = [
    {
        "id": "employees_combined",
        "task": "How many employees do Acme and Initech have combined?",
        "expected": 1287,
        "note": "single tool, two lookups + addition",
        "tool": "get_employee_count",
        "test_case": {
            "pattern": "map_reduce",
            "input": ["Acme", "Initech"],
            "expected": 1287,
        },
    },
    {
        "id": "currency_simple",
        "task": "How much is 100 USD in EUR?",
        "expected": 90.0,
        "note": "different tool - single parameterized call",
        "tool": "convert_currency",
        "test_case": {
            "pattern": "single_call",
            "input": {"amount": 100, "from_currency": "USD", "to_currency": "EUR"},
            "expected": 90.0,
        },
    },
    {
        "id": "population_single",
        "task": "What is the population of Tokyo?",
        "expected": 14_000_000,
        "note": "single lookup, no arithmetic",
        "tool": "get_city_population",
        "test_case": {
            "pattern": "map_reduce",
            "input": ["Tokyo"],
            "expected": 14_000_000,
        },
    },
    {
        "id": "two_tools",
        "task": "What is the combined population of Paris and Delhi, converted to millions?",
        "expected": 34.1,
        "note": "harder: two lookups + arithmetic",
        "tool": "get_city_population",
        "test_case": {
            "pattern": "map_reduce",
            "input": ["Paris", "Delhi"],
            "expected": 34100000,
        },
    },
    {
        "id": "no_tool",
        "task": "What is 25 multiplied by 4?",
        "expected": 100,
        "note": "no tool needed - tests over-reaching",
        "tool": None,
        "test_case": None,
    },
]
