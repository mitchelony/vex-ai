def diverter_should_spin(*, route: str, now_ms: int, last_valid_color_seen_ms, timeout_ms: int) -> bool:
    if route not in {"alliance", "opponent"}:
        return False

    if last_valid_color_seen_ms is None:
        return False

    return now_ms - last_valid_color_seen_ms <= timeout_ms
