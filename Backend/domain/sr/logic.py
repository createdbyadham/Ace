"""
SM-2 Spaced Repetition Algorithm

Quality mapping:
- got_it (Correct) → quality = 5
- meh              → quality = 3  
- forgot           → quality = 1

SM-2 rules:
- quality < 3: reset repetition, short interval
- quality >= 3: increment repetition, calculate interval using EF
- EF is adjusted based on quality (min 1.3)
"""

from dataclasses import dataclass


# Quality mapping from response strings
QUALITY_MAP = {
    "got_it": 5,
    "meh": 3,
    "forgot": 1,
}


@dataclass
class SM2Result:
    """Result of SM-2 calculation."""
    repetition: int
    interval_days: int
    ef: float
    quality: int


def map_response_to_quality(response: str) -> int:
    """Map response string to SM-2 quality score."""
    normalized = response.lower()
    if normalized not in QUALITY_MAP:
        raise ValueError(f"Unknown response: {response}. Must be one of: {list(QUALITY_MAP.keys())}")
    return QUALITY_MAP[normalized]


def compute_sm2(
    prev_repetition: int,
    prev_interval: int,
    prev_ef: float,
    response: str,
) -> SM2Result:
    """
    Compute new SM-2 state based on response.
    
    Args:
        prev_repetition: Current repetition count
        prev_interval: Current interval in days
        prev_ef: Current easiness factor (1.3 - 5.0)
        response: User response ('forgot', 'meh', 'got_it')
    
    Returns:
        SM2Result with new repetition, interval, ef, and quality
    """
    quality = map_response_to_quality(response)
    
    # Calculate new EF (easiness factor)
    # Formula: EF' = EF + (0.1 - (5 - q) * (0.08 + (5 - q) * 0.02))
    new_ef = prev_ef + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    
    # EF must not go below 1.3
    if new_ef < 1.3:
        new_ef = 1.3
    # Cap at 5.0
    if new_ef > 5.0:
        new_ef = 5.0
    
    # Determine new repetition and interval
    if quality < 3:
        # Failed: reset to beginning
        new_repetition = 0
        new_interval = 1  # Review again tomorrow
    else:
        # Passed: increment repetition and calculate interval
        new_repetition = prev_repetition + 1
        
        if new_repetition == 1:
            new_interval = 1
        elif new_repetition == 2:
            new_interval = 6
        else:
            # For repetition > 2: interval = previous_interval * EF
            new_interval = round(prev_interval * new_ef)
            
            # Minimum interval of 1 day
            if new_interval < 1:
                new_interval = 1
    
    return SM2Result(
        repetition=new_repetition,
        interval_days=new_interval,
        ef=round(new_ef, 2),
        quality=quality,
    )


__all__ = [
    "SM2Result",
    "QUALITY_MAP",
    "map_response_to_quality",
    "compute_sm2",
]
