
import os
import time

from dotenv import load_dotenv
from google import genai
from google.genai import types


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


client = genai.Client(api_key=API_KEY)


def generate_answer(prompt, max_retries=3):

    if not prompt or not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

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

            return answer.strip()

        except Exception as error:

            error_message = str(error)

            retryable = any(
                code in error_message
                for code in ["503", "429", "500", "504"]
            )

            if not retryable:
                raise

            if attempt == max_retries - 1:
                raise

            wait_time = 2 ** (attempt + 1)

            print(
                f"Gemini temporarily unavailable. "
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)

    raise RuntimeError("Gemini request failed.")
