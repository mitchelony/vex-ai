def latched_storage_route(previous_route: str, detected_color: str, alliance_color: str) -> str:
    if detected_color == "unknown":
        return previous_route

    if detected_color == alliance_color:
        return "alliance"

    return "opponent"
