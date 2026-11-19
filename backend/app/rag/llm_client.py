import os
import time
import logging
import re

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

logger = logging.getLogger(__name__)

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-flash-latest"
)

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. Check your .env file."
    )

client = genai.Client(api_key=API_KEY)


class GeminiServiceError(Exception):
    """Represents a Gemini API failure."""

    def __init__(
        self,
        message,
        status_code=503,
        sources=None
    ):
        super().__init__(message)

        self.status_code = status_code
        self.sources = sources or []

        self.user_message = message


def get_error_code(error):

    code = getattr(error, "code", None)

    if code is None:
        code = getattr(error, "status_code", None)

    if code is not None:
        try:
            return int(code)
        except (ValueError, TypeError):
            pass

    match = re.search(
        r"\b(400|401|403|404|429|500|502|503|504)\b",
        str(error)
    )

    if match:
        return int(match.group(1))

    return None


def generate_answer(prompt, max_retries=3):

    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    if not isinstance(max_retries, int) or max_retries < 1:
        raise ValueError("max_retries must be at least 1.")

    for attempt in range(max_retries):

        try:

            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.2,
                    max_output_tokens=1024
                )
            )

            answer = response.text

            if not answer or not answer.strip():
                raise GeminiServiceError(
                    "Gemini returned an empty response.",
                    status_code=502
                )

            logger.info(
                "Gemini response generated successfully."
            )

            return answer.strip()

        except GeminiServiceError:
            raise

        except Exception as error:

            status_code = get_error_code(error)

            error_message = str(error)

            # Do not retry quota errors.
            if status_code == 429:

                logger.error(
                    "Gemini quota/rate limit error: %s",
                    error_message
                )

                raise GeminiServiceError(
                    "Gemini API quota or rate limit exceeded. "
                    "Check your Google AI Studio quota and billing.",
                    status_code=429
                ) from error
            retryable = status_code in (500, 503, 504)

            if retryable and attempt < max_retries - 1:

                wait_time = 2 ** (attempt + 1)

                logger.warning(
                    "Gemini temporarily unavailable. "
                    "Attempt %s/%s. Retrying in %s seconds.",
                    attempt + 1,
                    max_retries,
                    wait_time
                )

                time.sleep(wait_time)
                continue

            if status_code in (500, 503, 504):

                logger.error(
                    "Gemini failed after %s attempts: %s",
                    max_retries,
                    error_message
                )

                raise GeminiServiceError(
                    "Gemini is temporarily unavailable. "
                    "Please try again later.",
                    status_code=status_code
                ) from error

            logger.exception("Gemini API request failed.")

            raise GeminiServiceError(
                "Unable to generate an AI response. "
                "Please check your API configuration.",
                status_code=status_code or 502
            ) from error

    raise GeminiServiceError(
        "Gemini request failed.",
        status_code=503
    )
