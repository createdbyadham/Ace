import math


def compute_new_interval_and_repetition(
    prev_repetition: int, prev_interval: int, response: str
) -> tuple[int, int]:
    """
    Spaced repetition logic for the three-button flow.
    Returns (new_repetition, new_interval_days).
    """
    normalized = response.lower()
    if normalized == "forgot":
        new_repetition = 0
        new_interval = 1
    elif normalized == "meh":
        new_repetition = prev_repetition + 1
        if prev_interval <= 0:
            new_interval = 1
        else:
            new_interval = max(1, math.ceil(prev_interval * 1.2))
    elif normalized == "got_it":
        new_repetition = prev_repetition + 1
        if new_repetition == 1:
            new_interval = 1
        elif new_repetition == 2:
            new_interval = 6
        else:
            new_interval = max(1, round(prev_interval * 2) if prev_interval > 0 else 6)
    else:
        raise ValueError("Unknown response")

    return new_repetition, int(new_interval)


__all__ = ["compute_new_interval_and_repetition"]

