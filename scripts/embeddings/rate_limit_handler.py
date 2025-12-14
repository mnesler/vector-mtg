"""
Rate limit handler for LLM API calls.

Handles rate limiting errors from Anthropic Claude API and other providers,
including parsing retry headers and implementing backoff strategies.
"""

import time
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def handle_rate_limit(
    error: Exception,
    default_wait: int = 60,
    buffer_seconds: int = 1
) -> int:
    """
    Handle rate limit errors by waiting for the appropriate amount of time.

    When the Claude API returns a rate limit error (HTTP 429), it includes headers
    that tell us when we can retry. This function parses those headers and sleeps
    for the required duration.

    Args:
        error: The RateLimitError exception from the Anthropic API
        default_wait: Default wait time in seconds if no header info available
        buffer_seconds: Extra seconds to add to wait time for safety

    Returns:
        int: The number of seconds we waited (excluding buffer)

    Rate limit response headers:
        - retry-after: Seconds to wait before retrying (string)
        - x-ratelimit-limit-requests: Total requests allowed per period
        - x-ratelimit-remaining-requests: Requests remaining (usually "0")
        - x-ratelimit-reset-requests: Unix timestamp when limit resets

    Example Claude API response when rate limited:
        HTTP/1.1 429 Too Many Requests
        {
            "error": {
                "type": "rate_limit_error",
                "message": "Number of request tokens has exceeded your per-minute rate limit..."
            }
        }
        Headers:
            retry-after: 20
            x-ratelimit-limit-requests: 50
            x-ratelimit-remaining-requests: 0
            x-ratelimit-reset-requests: 1702934567.123
    """
    wait_time = default_wait

    # Try to get wait time from response headers
    if hasattr(error, 'response') and hasattr(error.response, 'headers'):
        headers = error.response.headers

        # Option 1: Use retry-after header (preferred)
        if 'retry-after' in headers:
            try:
                wait_time = int(headers['retry-after'])
                logger.warning(
                    f"Rate limit hit. retry-after header says wait {wait_time}s. "
                    f"Remaining: {headers.get('x-ratelimit-remaining-requests', 'unknown')}"
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse retry-after header: {e}")

        # Option 2: Calculate from reset timestamp
        elif 'x-ratelimit-reset-requests' in headers:
            try:
                reset_time = float(headers['x-ratelimit-reset-requests'])
                current_time = time.time()
                wait_time = max(0, int(reset_time - current_time))
                logger.warning(
                    f"Rate limit hit. Calculated {wait_time}s wait from reset timestamp. "
                    f"Limit: {headers.get('x-ratelimit-limit-requests', 'unknown')}"
                )
            except (ValueError, TypeError) as e:
                logger.warning(f"Failed to parse reset timestamp: {e}")
        else:
            logger.warning(
                f"Rate limit hit but no retry headers found. "
                f"Using default wait time: {default_wait}s"
            )
    else:
        logger.warning(
            f"Rate limit error has no response headers. "
            f"Using default wait time: {default_wait}s"
        )

    # Add buffer for safety and sleep
    total_wait = wait_time + buffer_seconds
    logger.info(f"Waiting {wait_time}s (+{buffer_seconds}s buffer) before retrying...")
    time.sleep(total_wait)

    return wait_time
