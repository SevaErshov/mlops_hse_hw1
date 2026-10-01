import math
from datetime import datetime


def preprocess(row):
    if not isinstance(row, dict):
        raise ValueError("Транзакция должна быть JSON-объектом")
    time = datetime.fromisoformat(str(row["transaction_time"]))
    numbers = {}
    for name in ("amount", "lat", "lon", "merchant_lat", "merchant_lon", "population_city"):
        value = float(row[name])
        if not math.isfinite(value):
            raise ValueError(f"Некорректное число: {name}")
        numbers[name] = value
    if numbers["amount"] < 0 or numbers["population_city"] < 0:
        raise ValueError("Сумма и население не могут быть отрицательными")
    for name, limit in (("lat", 90), ("merchant_lat", 90), ("lon", 180), ("merchant_lon", 180)):
        if abs(numbers[name]) > limit:
            raise ValueError(f"Некорректная координата: {name}")
    lat1, lon1, lat2, lon2 = [math.radians(numbers[k]) for k in ("lat", "lon", "merchant_lat", "merchant_lon")]
    a = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
    return {
        "amount": numbers["amount"],
        "log_amount": math.log1p(numbers["amount"]),
        "hour": time.hour,
        "weekday": time.weekday(),
        "distance_km": 6371 * 2 * math.asin(math.sqrt(min(1, max(0, a)))),
        "population": math.log1p(numbers["population_city"]),
        "category": str(row.get("cat_id") or "unknown"),
        "gender": str(row.get("gender") or "unknown"),
        "state": str(row.get("us_state") or "unknown"),
    }
