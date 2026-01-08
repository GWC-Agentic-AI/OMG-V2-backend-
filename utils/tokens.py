import tiktoken
from config import settings


def count_tokens(text: str, model: str = None) -> int:
    """
    Calculate token count for given text
    
    Args:
        text: Input text to count tokens
        model: Model name (defaults to config model)
    
    Returns:
        Token count as integer
    """
    if model is None:
        model = settings.openai_model
    
    try:
        encoding = tiktoken.encoding_for_model(model)
    except KeyError:
        # Fallback to cl100k_base for unknown models
        encoding = tiktoken.get_encoding("cl100k_base")
    
    return len(encoding.encode(text))