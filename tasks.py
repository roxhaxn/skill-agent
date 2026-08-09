# 10 tasks. Each maps to a tool + a test_case used to VERIFY a distilled skill.
# Expected answers computed from the fake data in tools.py.

TASKS = [
    {"id": "employees_acme_initech",
     "task": "How many employees do Acme and Initech have combined?",
     "expected": 1287, "tool": "get_employee_count",
     "test_case": {"pattern": "map_reduce", "input": ["Acme", "Initech"], "expected": 1287}},

    {"id": "employees_stark_wayne",
     "task": "How many employees do Stark and Wayne have combined?",
     "expected": 20000, "tool": "get_employee_count",
     "test_case": {"pattern": "map_reduce", "input": ["Stark", "Wayne"], "expected": 20000}},

    {"id": "currency_usd_eur",
     "task": "How much is 100 USD in EUR?",
     "expected": 90.0, "tool": "convert_currency",
     "test_case": {"pattern": "single_call", "input": {"amount": 100, "from_currency": "USD", "to_currency": "EUR"}, "expected": 90.0}},

    {"id": "currency_gbp_inr",
     "task": "How much is 50 GBP in INR?",
     "expected": 5187.5, "tool": "convert_currency",
     "test_case": {"pattern": "single_call", "input": {"amount": 50, "from_currency": "GBP", "to_currency": "INR"}, "expected": 5187.5}},

    {"id": "population_tokyo",
     "task": "What is the population of Tokyo?",
     "expected": 14_000_000, "tool": "get_city_population",
     "test_case": {"pattern": "map_reduce", "input": ["Tokyo"], "expected": 14_000_000}},

    {"id": "population_london_cairo",
     "task": "What is the combined population of London and Cairo?",
     "expected": 29_000_000, "tool": "get_city_population",
     "test_case": {"pattern": "map_reduce", "input": ["London", "Cairo"], "expected": 29_000_000}},

    {"id": "stock_aapl_msft",
     "task": "What is the combined share price of AAPL and MSFT?",
     "expected": 600.0, "tool": "get_stock_price",
     "test_case": {"pattern": "map_reduce", "input": ["AAPL", "MSFT"], "expected": 600.0}},

    {"id": "distance_tokyo",
     "task": "How far is Tokyo from the hub in km?",
     "expected": 9560, "tool": "get_distance_km",
     "test_case": {"pattern": "map_reduce", "input": ["Tokyo"], "expected": 9560}},

    {"id": "temperature_delhi_cairo",
     "task": "What is the combined temperature of Delhi and Cairo in Celsius?",
     "expected": 65, "tool": "get_temperature_c",
     "test_case": {"pattern": "map_reduce", "input": ["Delhi", "Cairo"], "expected": 65}},

    {"id": "no_tool",
     "task": "What is 25 multiplied by 4?",
     "expected": 100, "tool": None, "test_case": None},
]
