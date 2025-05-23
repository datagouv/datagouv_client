from tenacity import (
    retry,
    retry_if_not_exception_type,
    stop_after_attempt,
    wait_exponential,
)


def log_retry_attempt(state):
    exception = state.outcome.exception()
    exception_name = type(exception).__name__
    exception_message = str(exception)
    print(f"Retrying {state.fn.__name__} due to {exception_name}: {exception_message}")


def _simple_connection_retry(
    always_raise_exceptions=(PermissionError, ValueError),
    attempts=5,
    func=log_retry_attempt,
    wait=wait_exponential(multiplier=1, min=4, max=10),
    reraise=True,
    **kwargs,
):
    return retry(
        retry=retry_if_not_exception_type(
            always_raise_exceptions
        ),  # Don't retry if these exceptions
        stop=stop_after_attempt(attempts),  # Stop after X attempts
        wait=wait,  # Exponential backoff
        before_sleep=func,  # Call this function before each retry
        reraise=reraise,  # Reraise the exception after all retries are exhausted,
        **kwargs,
    )


simple_connection_retry = _simple_connection_retry()
