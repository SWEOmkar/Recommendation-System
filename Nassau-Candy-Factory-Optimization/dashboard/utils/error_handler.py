"""Centralized error handling utilities for the Nassau Candy Dashboard.

Provides safe execution context managers and user-friendly error message
constants to prevent information leakage (stack traces, file paths, internal
details) while preserving full server-side logging for debugging.
"""

import logging
import traceback
from contextlib import contextmanager

import streamlit as st

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Generic user-facing error messages (no internal details)
# ---------------------------------------------------------------------------
DATA_LOAD_ERROR = (
    "Unable to load the required dataset. "
    "Please contact the operations team if this issue persists."
)
MODEL_LOAD_ERROR = (
    "The prediction model could not be initialized. "
    "Please contact the operations team if this issue persists."
)
RECOMMENDATION_ERROR = (
    "An error occurred while generating recommendations. "
    "Please try again or contact the operations team."
)
SIMULATION_ERROR = (
    "An error occurred while running the simulation. "
    "Please try adjusting your parameters or contact the operations team."
)
CHART_RENDER_ERROR = (
    "Unable to render this visualization. "
    "Please try refreshing the page."
)
PAGE_RENDER_ERROR = (
    "An unexpected error occurred while loading this page. "
    "Please try refreshing or contact the operations team."
)
PREPROCESSING_ERROR = (
    "A data processing error occurred. "
    "Please verify the input data and try again."
)


@contextmanager
def safe_page_execution(page_name: str, user_message: str = PAGE_RENDER_ERROR):
    """Context manager that catches all exceptions on a Streamlit page.

    Logs full error details server-side and shows a generic message to the user.

    Usage::

        with safe_page_execution("Recommendations"):
            render_recommendations_page(df)

    Args:
        page_name: Human-readable name for logging context.
        user_message: Generic message shown to the user on failure.
    """
    try:
        yield
    except Exception:
        logger.exception("Unhandled error on page '%s'", page_name)
        st.error(user_message)


def log_and_reraise(error: Exception, context: str, user_message: str) -> None:
    """Logs full exception details and re-raises with a sanitized message.

    Args:
        error: The original exception.
        context: Description of what was happening when the error occurred.
        user_message: Sanitized message safe to show to users.
    """
    logger.error(
        "%s — %s: %s\n%s",
        context,
        type(error).__name__,
        str(error),
        traceback.format_exc(),
    )
    raise type(error)(user_message) from None
