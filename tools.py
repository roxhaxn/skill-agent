from smolagents import tool


@tool
def get_employee_count(company: str) -> int:
    """Returns the number of employees at a given company.

    Args:
        company: The name of the company to look up.
    """
    fake_db = {"acme": 1200, "globex": 34000, "initech": 87}
    return fake_db.get(company.lower(), -1)


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Converts an amount of money from one currency to another using fixed rates.

    Args:
        amount: The amount of money to convert.
        from_currency: The 3-letter source currency code, e.g. 'USD'.
        to_currency: The 3-letter target currency code, e.g. 'EUR'.
    """
    # Fixed rates relative to USD, so answers are deterministic.
    usd_rates = {"usd": 1.0, "eur": 0.90, "gbp": 0.80, "inr": 83.0}
    amount_in_usd = amount / usd_rates[from_currency.lower()]
    return round(amount_in_usd * usd_rates[to_currency.lower()], 2)


@tool
def get_city_population(city: str) -> int:
    """Returns the population of a given city.

    Args:
        city: The name of the city to look up.
    """
    fake_db = {"paris": 2_100_000, "tokyo": 14_000_000, "delhi": 32_000_000}
    return fake_db.get(city.lower(), -1)


# Registry: skill name -> real function
TOOL_REGISTRY = {
    "get_employee_count": get_employee_count,
    "convert_currency": convert_currency,
    "get_city_population": get_city_population,
}