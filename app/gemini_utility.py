"""Utility class for interacting with Google Gemini via VertexAI to extract structured data."""

import json
import logging
import time
from typing import Dict, Optional

from google import genai
import requests
from requests.exceptions import RequestException

from .config import get_settings
from .exceptions import LLMAPIError, LLMContentError, LLMJsonParsingError

logger = logging.getLogger(__name__)


class GeminiUtility:
    """
    Utility class for interacting with Google Gemini via VertexAI to extract structured data.
    """

    _client = None

    @classmethod
    def _get_client(cls):
        """Initialize and return the Gemini client."""
        if cls._client is None:
            config = get_settings()
            if not config.LLM_API_KEY:
                logger.warning(
                    "LLM_API_KEY is not configured. Cannot initialize Gemini client."
                )
                raise LLMAPIError("LLM_API_KEY is not configured")

            # Initialize the client with API key
            cls._client = genai.Client(api_key=config.LLM_API_KEY)
            logger.info("Initialized Gemini client")

        return cls._client

    @staticmethod
    def _construct_prompt(html_snippet: str) -> str:
        """Constructs the prompt for the LLM."""
        return f"""
Extract the address information (address, city, state, zip_code) from the following HTML snippet.
Return the result as a JSON object with the following structure:
{{"address": "string | null", "city": "string | null", "state": "string | null", "zip_code": "string | null"}}
If a field cannot be found, use null for its value. Only return the JSON object, nothing else.

HTML Snippet:
```html
{html_snippet}
```

JSON Output:
"""

    @classmethod
    def extract_address_from_html(
        cls, html_snippet: str
    ) -> Optional[Dict[str, Optional[str]]]:
        """
        Sends an HTML snippet to Google Gemini via VertexAI to extract address details.

        Args:
            html_snippet: The HTML text containing potential address information.

        Returns:
            A dictionary with extracted address components ('address', 'city', 'state', 'zip_code')
            or None if extraction fails after retries or due to errors.

        Raises:
            LLMAPIError: If there's a persistent issue connecting to the Gemini API.
            LLMContentError: If the Gemini response indicates an issue (e.g., moderation).
            LLMJsonParsingError: If the Gemini response is not valid JSON.
        """
        config = get_settings()
        if not config.LLM_API_KEY:
            logger.warning("LLM_API_KEY is not configured. Skipping Gemini extraction.")
            return None

        # Get the model ID from configuration
        model_id = config.MODEL_ID
        if not model_id:
            model_id = "gemini-2.0-flash-001"  # Default model
            logger.info(f"MODEL_ID not specified, using default: {model_id}")

        # Construct the prompt for the model
        prompt = cls._construct_prompt(html_snippet)

        # Configure generation parameters
        generation_config = {
            "temperature": 0.2,
            "max_output_tokens": 1024,
            "top_p": 0.95,
        }

        last_exception = None

        # Try with retries
        for attempt in range(config.LLM_MAX_RETRIES):
            try:
                # Get client
                client = cls._get_client()

                # Get model
                model = client.models.get(model_id)

                # Generate content
                response = model.generate_content(
                    contents=prompt,
                    generation_config=generation_config
                )

                # Check for safety issues in the response
                if hasattr(response, "prompt_feedback") and response.prompt_feedback:
                    if hasattr(response.prompt_feedback, "block_reason") and response.prompt_feedback.block_reason:
                        error_msg = f"Gemini response blocked due to content moderation: {response.prompt_feedback.block_reason}"
                        logger.warning(error_msg)
                        raise LLMContentError(error_msg)

                # Get the text response
                if not response.text:
                    raise LLMContentError("Received empty response from Gemini")

                # Process the text response
                llm_output_text = response.text.strip()

                # Clean potential markdown code fences if the LLM includes them
                if llm_output_text.startswith("```json"):
                    llm_output_text = llm_output_text[7:]
                if llm_output_text.endswith("```"):
                    llm_output_text = llm_output_text[:-3]
                llm_output_text = llm_output_text.strip()

                try:
                    # Parse the JSON response
                    extracted_data = json.loads(llm_output_text)

                    # Basic validation of expected keys
                    expected_keys = {"address", "city", "state", "zip_code"}
                    if not expected_keys.issubset(extracted_data.keys()):
                        logger.warning(
                            f"Gemini JSON missing expected keys: {extracted_data}"
                        )
                        raise LLMJsonParsingError("Gemini JSON missing expected keys")

                    # Normalize empty strings to None if desired by spec
                    for key in expected_keys:
                        if extracted_data.get(key) == "":
                            extracted_data[key] = None

                    logger.info(
                        f"Successfully extracted address via Gemini: {extracted_data}"
                    )
                    return extracted_data

                except json.JSONDecodeError as e:
                    logger.error(
                        f"Failed to parse JSON from Gemini response: {llm_output_text}",
                        exc_info=True,
                    )
                    raise LLMJsonParsingError(f"Failed to parse JSON: {e}") from e

            except (LLMContentError, LLMJsonParsingError) as e:
                # Don't retry on content or parsing errors
                logger.error(f"Gemini processing error: {e}")
                raise e  # Propagate the specific error

            except Exception as e:
                logger.warning(
                    f"Gemini API request failed (attempt {attempt + 1}/{config.LLM_MAX_RETRIES}): {e}"
                )
                last_exception = e
                if attempt < config.LLM_MAX_RETRIES - 1:
                    time.sleep(config.LLM_RETRY_DELAY_SECONDS)
                else:
                    logger.error("Gemini API request failed after multiple retries.")
                    raise LLMAPIError(f"API request failed: {str(e)}") from e

        # Fallback if the loop completes without success or exception
        logger.error("Gemini extraction failed unexpectedly after loop completion.")
        if last_exception:
            raise LLMAPIError(
                f"Gemini extraction failed: {str(last_exception)}"
            ) from last_exception
        else:
            raise LLMAPIError(
                "Gemini extraction failed after all retries (unknown error)"
            )


if __name__ == "__main__":
    # Configure logging for standalone testing
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # To run this test block:
    # 1. Create a .env file in the project root (TrailBlazeApp-Scrapers)
    # 2. Add your Gemini API key:
    #    LLM_API_KEY="YOUR_API_KEY_HERE"
    #    MODEL_ID="gemini-2.0-flash-001"
    # 3. Or set environment variables:
    #    export LLM_API_KEY="YOUR_API_KEY"
    #    export MODEL_ID="gemini-2.0-flash-001"

    # For local development, you might want to use dotenv:
    # from dotenv import load_dotenv
    # load_dotenv()

    # Use the same settings mechanism as the rest of the application
    settings = get_settings()

    # Check API key and model ID
    if not settings.LLM_API_KEY:
        print("\nWARNING: LLM_API_KEY environment variable not set.")
        print(
            "Skipping live Gemini test. Create/check .env file or set environment variables."
        )
    else:
        model_id = settings.MODEL_ID or "gemini-2.0-flash-001"
        print(f"--- Testing Gemini Utility with Model ID: {model_id} ---")

        sample_html = """
        <div class="contact-info">
            <p>John Doe</p>
            <span>123 Main St<br/>Anytown, CA 90210</span>
            <p>Phone: 555-1234</p>
        </div>
        """
        try:
            address_data = GeminiUtility.extract_address_from_html(sample_html)
            if address_data:
                print("Extracted Address Data:")
                print(json.dumps(address_data, indent=2))
            else:
                # This case might indicate an issue if an exception wasn't raised
                print("Failed to extract address data (returned None). Check logs.")
        except (LLMAPIError, LLMContentError, LLMJsonParsingError) as e:
            print(f"An error occurred during Gemini extraction: {e}")
        except Exception as e:
            print(f"An unexpected error occurred during test: {e}")
