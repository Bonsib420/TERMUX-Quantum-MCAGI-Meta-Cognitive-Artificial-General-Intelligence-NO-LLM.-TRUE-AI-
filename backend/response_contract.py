def normalize_response(x):
    if isinstance(x, list):
        return " ".join(map(str, x))
    if isinstance(x, dict):
        return str(x.get("winner") or x.get("text") or x)
    return str(x)
