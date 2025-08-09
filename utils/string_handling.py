import re

def wildcard_to_regex(text: str) -> str:
    """
    Converts a wildcard string from the blocklist module to a regex pattern.
    - ? matches a single occurrence of any non-whitespace character.
    - * matches any number of any non-whitespace character.
    - ** matches any number of any character (including spaces).
    """
    # Escape all special regex characters first
    pattern = re.escape(text)
    # Convert our custom wildcards to regex syntax
    pattern = pattern.replace(r'\*\*', r'.*')  # ** -> .* (any character, any number, greedy)
    pattern = pattern.replace(r'\*', r'\S+')   # * -> \S+ (any non-whitespace, one or more)
    pattern = pattern.replace(r'\?', r'\S')    # ?  -> \S  (any non-whitespace, exactly one)
    
    # Return as a case-insensitive pattern with word boundaries for better matching
    return f"(?i)\\b{pattern}\\b"
