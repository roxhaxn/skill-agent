from smolagents import tool


@tool
def get_employee_count(company: str) -> int:
    """Returns the number of employees at a given company.

    Args:
        company: The name of the company to look up.
    """
    fake_db = {"acme": 1200, "globex": 34000, "initech": 87,
               "umbrella": 5000, "stark": 12000, "wayne": 8000}
    return fake_db.get(company.lower(), -1)


@tool
def convert_currency(amount: float, from_currency: str, to_currency: str) -> float:
    """Converts an amount of money from one currency to another using fixed rates.

    Args:
        amount: The amount of money to convert.
        from_currency: The 3-letter source currency code, e.g. 'USD'.
        to_currency: The 3-letter target currency code, e.g. 'EUR'.
    """
    usd_rates = {"usd": 1.0, "eur": 0.90, "gbp": 0.80, "inr": 83.0, "jpy": 150.0}
    amount_in_usd = amount / usd_rates[from_currency.lower()]
    return round(amount_in_usd * usd_rates[to_currency.lower()], 2)


@tool
def get_city_population(city: str) -> int:
    """Returns the population of a given city.

    Args:
        city: The name of the city to look up.
    """
    fake_db = {"paris": 2_100_000, "tokyo": 14_000_000, "delhi": 32_000_000,
               "london": 9_000_000, "cairo": 20_000_000, "lagos": 15_000_000}
    return fake_db.get(city.lower(), -1)


@tool
def get_stock_price(ticker: str) -> float:
    """Returns the current share price (in USD) for a stock ticker.

    Args:
        ticker: The stock ticker symbol, e.g. 'AAPL'.
    """
    fake_db = {"aapl": 200.0, "msft": 400.0, "goog": 150.0,
               "amzn": 180.0, "tsla": 250.0}
    return fake_db.get(ticker.lower(), -1.0)


@tool
def get_distance_km(city: str) -> int:
    """Returns the distance in km from a reference hub to the given city.

    Args:
        city: The destination city name.
    """
    fake_db = {"paris": 340, "london": 0, "tokyo": 9560,
               "delhi": 6700, "cairo": 3500, "lagos": 5000}
    return fake_db.get(city.lower(), -1)


@tool
def get_temperature_c(city: str) -> int:
    """Returns the current temperature in Celsius for a city.

    Args:
        city: The city name.
    """
    fake_db = {"paris": 18, "tokyo": 22, "delhi": 35,
               "london": 15, "cairo": 30, "lagos": 28}
    return fake_db.get(city.lower(), -999)


TOOL_REGISTRY = {
    "get_employee_count": get_employee_count,
    "convert_currency": convert_currency,
    "get_city_population": get_city_population,
    "get_stock_price": get_stock_price,
    "get_distance_km": get_distance_km,
    "get_temperature_c": get_temperature_c,
}
