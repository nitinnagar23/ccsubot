import re
from datetime import timedelta

def parse_duration(duration_str: str) -> timedelta | None:
    """
    Parses a duration string (e.g., '5w', '3d', '12h', '30m', '10s') into a timedelta object.
    Returns None if the format is invalid.
    """
    if not duration_str:
        return None
    
    match = re.match(r"(\d+)([smhdw])", duration_str.lower())
    if not match:
        return None
        
    value, unit = match.groups()
    value = int(value)
    
    if unit == 's':
        return timedelta(seconds=value)
    elif unit == 'm':
        return timedelta(minutes=value)
    elif unit == 'h':
        return timedelta(hours=value)
    elif unit == 'd':
        return timedelta(days=value)
    elif unit == 'w':
        return timedelta(weeks=value)
    return None

def humanize_delta(td: timedelta) -> str:
    """Converts a timedelta object to a human-readable string."""
    if not td or td.total_seconds() == 0:
        return "Not set"
        
    days = td.days
    hours, remainder = divmod(td.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    parts = []
    if days > 0:
        parts.append(f"{days} day{'s' if days > 1 else ''}")
    if hours > 0:
        parts.append(f"{hours} hour{'s' if hours > 1 else ''}")
    if minutes > 0:
        parts.append(f"{minutes} minute{'s' if minutes > 1 else ''}")
    if seconds > 0:
        parts.append(f"{seconds} second{'s' if seconds > 1 else ''}")
        
    return ", ".join(parts) if parts else "0 seconds"
