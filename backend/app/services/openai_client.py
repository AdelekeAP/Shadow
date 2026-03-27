"""
Shared OpenAI Client - Singleton client with retry, fallback, and circuit breaker
"""
import os
import random
import time
import logging
import threading
from enum import Enum
from typing import Optional, List, Any
from dataclasses import dataclass

from openai import OpenAI

logger = logging.getLogger(__name__)

# Model fallback chains (primary → capable fallback → budget fallback)
CHAT_MODELS = ["gpt-5.4", "gpt-4.1", "gpt-4.1-mini"]
PLAN_MODELS = ["gpt-4.1", "gpt-5.4", "gpt-4.1-mini"]


class OpenAIErrorType(str, Enum):
    rate_limit = "rate_limit"
    timeout = "timeout"
    quota_exceeded = "quota_exceeded"
    api_error = "api_error"
    invalid_request = "invalid_request"
    auth_error = "auth_error"
    circuit_open = "circuit_open"
    unknown = "unknown"


ERROR_MESSAGES = {
    OpenAIErrorType.rate_limit: "The AI is receiving too many requests. Please wait a moment and try again.",
    OpenAIErrorType.timeout: "The AI took too long to respond. Please try again with a shorter question.",
    OpenAIErrorType.quota_exceeded: "The AI service has reached its usage limit. Please try again later.",
    OpenAIErrorType.circuit_open: "The AI service is temporarily paused due to repeated errors. Please wait a minute.",
    OpenAIErrorType.api_error: "The AI service is temporarily unavailable. Please try again in a moment.",
    OpenAIErrorType.invalid_request: "There was a problem with the request. Please try rephrasing your message.",
    OpenAIErrorType.auth_error: "AI service authentication failed. Please contact support.",
    OpenAIErrorType.unknown: "An unexpected error occurred. Please try again.",
}


@dataclass
class OpenAIError(Exception):
    error_type: OpenAIErrorType
    user_message: str
    original_error: Optional[Exception] = None

    def __str__(self):
        return self.user_message


# --- Singleton client ---

_client: Optional[OpenAI] = None
_client_lock = threading.Lock()


def get_openai_client() -> Optional[OpenAI]:
    """Return a singleton OpenAI client instance."""
    global _client
    if _client is not None:
        return _client

    with _client_lock:
        if _client is not None:
            return _client
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OPENAI_API_KEY not found in environment variables")
            return None
        try:
            _client = OpenAI(api_key=api_key, timeout=60.0)
            logger.info("OpenAI client initialized (shared singleton)")
            return _client
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            return None


# --- Error classification ---

def classify_error(exc: Exception) -> OpenAIError:
    """Map an OpenAI SDK exception to a structured OpenAIError."""
    from openai import (
        RateLimitError,
        APITimeoutError,
        BadRequestError,
        AuthenticationError,
        APIError,
        APIConnectionError,
    )

    if isinstance(exc, RateLimitError):
        msg = str(exc).lower()
        if "quota" in msg or "billing" in msg:
            err_type = OpenAIErrorType.quota_exceeded
        else:
            err_type = OpenAIErrorType.rate_limit
    elif isinstance(exc, APITimeoutError):
        err_type = OpenAIErrorType.timeout
    elif isinstance(exc, BadRequestError):
        err_type = OpenAIErrorType.invalid_request
    elif isinstance(exc, AuthenticationError):
        err_type = OpenAIErrorType.auth_error
    elif isinstance(exc, APIConnectionError):
        err_type = OpenAIErrorType.api_error
    elif isinstance(exc, APIError):
        err_type = OpenAIErrorType.api_error
    else:
        err_type = OpenAIErrorType.unknown

    return OpenAIError(
        error_type=err_type,
        user_message=ERROR_MESSAGES[err_type],
        original_error=exc,
    )


# --- Circuit breaker ---

class CircuitBreaker:
    """
    Trips after `failure_threshold` failures within `window_seconds`,
    blocks for `recovery_seconds`, then half-opens to allow one retry.
    """

    def __init__(
        self,
        failure_threshold: int = 3,
        window_seconds: float = 300,  # 5 min
        recovery_seconds: float = 60,
    ):
        self._lock = threading.Lock()
        self._failures: list[float] = []
        self._tripped_at: Optional[float] = None
        self._half_open: bool = False
        self.failure_threshold = failure_threshold
        self.window_seconds = window_seconds
        self.recovery_seconds = recovery_seconds

    def record_failure(self):
        with self._lock:
            now = time.time()
            # If half-open probe failed, re-trip immediately
            if self._half_open:
                self._half_open = False
                self._tripped_at = now
                logger.warning("Circuit breaker half-open probe FAILED — re-tripping")
                return
            self._failures.append(now)
            # Prune old failures outside the window
            cutoff = now - self.window_seconds
            self._failures = [t for t in self._failures if t > cutoff]
            if len(self._failures) >= self.failure_threshold:
                self._tripped_at = now
                logger.warning("Circuit breaker TRIPPED — blocking OpenAI calls")

    def record_success(self):
        with self._lock:
            self._half_open = False
            self._failures.clear()
            self._tripped_at = None

    def is_open(self) -> bool:
        with self._lock:
            if self._tripped_at is None:
                return False
            elapsed = time.time() - self._tripped_at
            if elapsed >= self.recovery_seconds:
                # Half-open: allow ONE probe request without clearing failures
                self._half_open = True
                logger.info("Circuit breaker half-open — allowing one probe request")
                return False
            return True


_circuit_breaker = CircuitBreaker()


# --- Retry with fallback ---

def call_with_retry(
    messages: list,
    models: Optional[List[str]] = None,
    max_retries: int = 2,
    timeout: float = 30.0,
    stream: bool = False,
    **kwargs: Any,
):
    """
    Call OpenAI chat completions with retry + model fallback.

    Args:
        messages: Chat messages list
        models: Ordered list of models to try (defaults to CHAT_MODELS)
        max_retries: Retries per model before falling back
        timeout: Request timeout in seconds
        stream: Whether to return a streaming response
        **kwargs: Extra args passed to chat.completions.create

    Returns:
        OpenAI ChatCompletion (or stream iterator if stream=True)

    Raises:
        OpenAIError: On all failures after retries exhausted
    """
    client = get_openai_client()
    if client is None:
        raise OpenAIError(
            error_type=OpenAIErrorType.auth_error,
            user_message="OpenAI client not initialized. Please check OPENAI_API_KEY.",
        )

    if _circuit_breaker.is_open():
        raise OpenAIError(
            error_type=OpenAIErrorType.circuit_open,
            user_message=ERROR_MESSAGES[OpenAIErrorType.circuit_open],
        )

    if models is None:
        models = CHAT_MODELS

    last_error: Optional[OpenAIError] = None

    for model in models:
        for attempt in range(max_retries + 1):
            try:
                # Newer models (gpt-5.x, o-series) require max_completion_tokens
                # instead of max_tokens. Translate automatically.
                call_kwargs = dict(kwargs)
                if "max_tokens" in call_kwargs:
                    call_kwargs["max_completion_tokens"] = call_kwargs.pop("max_tokens")

                response = client.chat.completions.create(
                    model=model,
                    messages=messages,
                    stream=stream,
                    timeout=timeout,
                    **call_kwargs,
                )
                _circuit_breaker.record_success()
                logger.info(
                    "OpenAI call succeeded: model=%s, attempt=%d/%d",
                    model, attempt + 1, max_retries + 1,
                )
                return response

            except Exception as exc:
                classified = classify_error(exc)
                last_error = classified
                _circuit_breaker.record_failure()

                # Don't retry auth or invalid request errors
                if classified.error_type in (
                    OpenAIErrorType.auth_error,
                    OpenAIErrorType.invalid_request,
                    OpenAIErrorType.quota_exceeded,
                ):
                    raise classified

                # Exponential backoff with jitter before retry
                if attempt < max_retries:
                    delay = (2 ** attempt) + random.uniform(0, 0.5)
                    logger.warning(
                        f"OpenAI call failed ({model}, attempt {attempt + 1}): "
                        f"{classified.error_type.value} — retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                else:
                    logger.warning(
                        f"OpenAI call failed ({model}): exhausted retries, "
                        f"falling back to next model"
                    )
                    break  # Try next model

    # All models exhausted — log diagnostic details
    logger.error(
        f"OpenAI call_with_retry exhausted all models. "
        f"models_tried={models}, message_count={len(messages)}, "
        f"last_error={last_error.error_type.value if last_error else 'none'}"
    )
    raise last_error or OpenAIError(
        error_type=OpenAIErrorType.unknown,
        user_message=ERROR_MESSAGES[OpenAIErrorType.unknown],
    )
