
import os
import time
import logging

from dotenv import load_dotenv
from google import genai
from google.genai import types


# Load environment variables
load_dotenv()

API_KEY = os.getenv("GEMINI_API_KEY")

MODEL_NAME = os.getenv(
    "GEMINI_MODEL",
    "gemini-flash-latest"
)

if not API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing. "
        "Check your .env file."
    )


# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

logger = logging.getLogger(__name__)


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

            if not answer:
                raise RuntimeError(
                    "Gemini returned an empty response."
                )

            logger.info("Gemini response generated successfully.")

            return answer.strip()

        except Exception as error:

            error_message = str(error)

            retryable = any(
                code in error_message
                for code in ["503", "429", "500", "504"]
            )

            if not retryable:
                logger.exception("Gemini API request failed.")
                raise

            if attempt == max_retries - 1:
                logger.error(
                    "Gemini failed after %s attempts: %s",
                    max_retries,
                    error_message
                )
                raise

            wait_time = 2 ** (attempt + 1)

            logger.warning(
                "Gemini temporarily unavailable. "
                "Attempt %s/%s. Retrying in %s seconds.",
                attempt + 1,
                max_retries,
                wait_time
            )

            time.sleep(wait_time)

    raise RuntimeError("Gemini request failed.")
