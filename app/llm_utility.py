"""Utility class for interacting with an LLM endpoint to extract structured data."""

import json
import logging
import time
from typing import Dict, Optional

import requests
from requests.exceptions import RequestException

from .config import get_settings
from .exceptions import LLMAPIError, LLMContentError, LLMJsonParsingError

logger = logging.getLogger(__name__)


class LLM_Utility:
    """
    Utility class for interacting with an LLM endpoint to extract structured data.
    """

    @staticmethod
    def _construct_prompt(html_snippet: str) -> str:
        """Constructs the prompt for the LLM."""
        # Basic prompt, might need refinement based on the specific LLM's requirements
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
    def extract_address_from_html(cls, html_snippet: str) -> Optional[Dict[str, Optional[str]]]:
        """
        Sends an HTML snippet to the configured LLM endpoint to extract address details.

        Args:
            html_snippet: The HTML text containing potential address information.

        Returns:
            A dictionary with extracted address components ('address', 'city', 'state', 'zip_code')
            or None if extraction fails after retries or due to errors.

        Raises:
            LLMAPIError: If there's a persistent issue connecting to the LLM API.
            LLMContentError: If the LLM response indicates an issue (e.g., moderation).
            LLMJsonParsingError: If the LLM response is not valid JSON.
        """
        config = get_settings()
        if not config.LLM_API_KEY:
            logger.warning("LLM_API_KEY is not configured. Skipping LLM extraction.")
            return None

        # Determine which API URL to use (prefer the full LLM_API_URL if available)
        api_url = config.LLM_API_URL
        if not api_url:
            if not config.LLM_API_ENDPOINT or not config.MODEL_ID:
                logger.warning("Neither LLM_API_URL nor both LLM_API_ENDPOINT and MODEL_ID are configured. Skipping LLM extraction.")
                return None

            # Check if we're using Gemini 2.0 models which use a different API version
            if "2.0" in config.MODEL_ID:
                # Gemini 2.0 models use v1alpha/v1beta
                api_url = f"{config.LLM_API_ENDPOINT.rstrip('/')}/v1beta/models/{config.MODEL_ID}:generateContent"
            else:
                # Gemini 1.0 models use v1
                api_url = f"{config.LLM_API_ENDPOINT.rstrip('/')}/v1/models/{config.MODEL_ID}:generateContent"

            logger.info(f"Using constructed API URL: {api_url}")

        prompt = cls._construct_prompt(html_snippet)
        headers = {
            "Content-Type": "application/json",
        }

        # For Google's Gemini API, the API key is passed as a query parameter, not in the Authorization header
        if "?" not in api_url:
            api_url = f"{api_url}?key={config.LLM_API_KEY}"
        else:
            api_url = f"{api_url}&key={config.LLM_API_KEY}"

        logger.info(f"Using API URL with key: {api_url.split('?')[0]}?key=REDACTED")

        # Payload structure for Google's Gemini API v1
        payload = {
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": prompt}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "maxOutputTokens": 1024,  # Increased from 150 to allow for more complex responses
            }
        }

        last_exception: Optional[Exception] = LLMAPIError("LLM request failed after all retries.")  # Initialize with a default error

        for attempt in range(config.LLM_MAX_RETRIES):
            try:
                response = requests.post(
                    api_url,
                    headers=headers,
                    json=payload,
                    timeout=config.LLM_REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

                # --- LLM Response Handling for Gemini API ---
                # 1. Check for LLM-specific errors
                response_data = response.json()
                if response_data.get("error"):
                    error_msg = f"Gemini API error: {response_data['error']}"
                    logger.error(error_msg)
                    # Don't retry on definitive API errors returned in the response body
                    raise LLMContentError(error_msg)

                # Check for content filtering/safety issues
                if "promptFeedback" in response_data and response_data["promptFeedback"].get("blockReason"):
                    block_reason = response_data["promptFeedback"]["blockReason"]
                    logger.warning(f"Gemini response blocked due to content moderation: {block_reason}")
                    # Don't retry on content moderation blocks
                    raise LLMContentError(f"Gemini response blocked due to content moderation: {block_reason}")

                # 2. Extract the actual text content containing the JSON
                # Navigate Gemini API response structure
                llm_output_text = ""
                if "candidates" in response_data and response_data["candidates"]:
                    candidate = response_data["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                llm_output_text += part["text"]

                if not llm_output_text:
                    logger.error(f"Could not extract text from Gemini response: {response_data}")
                    # Don't retry if the response structure is wrong
                    raise LLMContentError("Could not extract text from Gemini response.")

                # 3. Parse the JSON
                try:
                    # Clean potential markdown code fences if the LLM includes them
                    if llm_output_text.startswith("```json"):
                        llm_output_text = llm_output_text[7:]
                    if llm_output_text.endswith("```"):
                        llm_output_text = llm_output_text[:-3]
                    llm_output_text = llm_output_text.strip()

                    extracted_data = json.loads(llm_output_text)

                    # Basic validation of expected keys
                    expected_keys = {"address", "city", "state", "zip_code"}
                    if not expected_keys.issubset(extracted_data.keys()):
                        logger.warning(f"LLM JSON missing expected keys: {extracted_data}")
                        # Decide if this is an error or just return partial data/None
                        # For now, treat as parsing error for simplicity
                        # Don't retry if the format is wrong
                        raise LLMJsonParsingError("LLM JSON missing expected keys.")

                    # Normalize empty strings to None if desired by spec
                    for key in expected_keys:
                        if extracted_data.get(key) == "":
                            extracted_data[key] = None

                    logger.info(f"Successfully extracted address via LLM: {extracted_data}")
                    return extracted_data

                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON from LLM response: {llm_output_text}", exc_info=True)
                    # Raise specific error to potentially handle differently upstream
                    raise LLMJsonParsingError(f"Failed to parse JSON: {e}") from e

            except (LLMContentError, LLMJsonParsingError) as e:
                # Don't retry on content or parsing errors from the LLM itself
                logger.error(f"LLM processing error: {e}")
                raise e  # Propagate the specific error

            except RequestException as e:
                logger.warning(f"LLM API request failed (attempt {attempt + 1}/{config.LLM_MAX_RETRIES}): {e}")
                last_exception = LLMAPIError(f"API request failed: {e}")
                if attempt < config.LLM_MAX_RETRIES - 1:
                    time.sleep(config.LLM_RETRY_DELAY_SECONDS)
                else:
                    logger.error("LLM API request failed after multiple retries.")
                    # Ensure last_exception is an Exception before raising
                    if isinstance(last_exception, Exception):
                        raise last_exception from e
                    else:  # Should not happen with the new initialization, but as a safeguard
                        raise LLMAPIError("LLM API request failed after multiple retries (unknown error).") from e

            except json.decoder.JSONDecodeError as e:  # Handle JSON decode errors separately
                logger.error(f"Failed to decode JSON from LLM API response (attempt {attempt + 1}): {e}", exc_info=True)
                # Don't retry JSON decode errors, treat them as parsing errors
                raise LLMJsonParsingError(f"Failed to parse JSON from API response: {e}") from e

            except (ValueError, TypeError, KeyError) as e:  # Catch other specific exceptions
                logger.error(f"Unexpected error during LLM interaction (attempt {attempt + 1}): {e}", exc_info=True)
                last_exception = e  # Store the exception
                if attempt < config.LLM_MAX_RETRIES - 1:
                    time.sleep(config.LLM_RETRY_DELAY_SECONDS)
                else:
                    logger.error("Unexpected error persisted after retries during LLM interaction.")
                    # Raise a generic error wrapping the last exception
                    raise LLMAPIError("An unexpected error occurred during LLM interaction.") from last_exception

        # This part should ideally not be reached if exceptions are always raised on failure.
        # If the loop completes without success or exception (e.g., MAX_RETRIES = 0),
        # raise the initialized default error.
        logger.error("LLM extraction failed unexpectedly after loop completion.")
        if isinstance(last_exception, Exception):
            raise last_exception  # Raise the last known error
        else:
            # Should not happen given initialization, but raise default if it does
            raise LLMAPIError("LLM extraction failed after all retries (default error).")


if __name__ == "__main__":
    # Configure logging for standalone testing
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # To run this test block:
    # 1. Create a .env file in the project root (TrailBlazeApp-Scrapers)
    # 2. Add your LLM endpoint, key, and model ID:
    #    LLM_API_ENDPOINT="https://generativelanguage.googleapis.com"
    #    LLM_API_KEY="YOUR_API_KEY_HERE"
    #    MODEL_ID="gemini-2.0-flash-lite"
    #    LLM_API_URL="https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:generateContent"
    # 3. Or set environment variables:
    #    export LLM_API_ENDPOINT="https://generativelanguage.googleapis.com"
    #    export LLM_API_KEY="YOUR_API_KEY"
    #    export MODEL_ID="gemini-2.0-flash-lite"
    #    export LLM_API_URL="https://generativelanguage.googleapis.com/v1beta/models/${MODEL_ID}:generateContent"

    # For local development, you might want to use dotenv:
    # from dotenv import load_dotenv
    # load_dotenv()

    # Use the same settings mechanism as the rest of the application
    settings = get_settings()

    # Check API key and either LLM_API_URL or both LLM_API_ENDPOINT and MODEL_ID
    if not settings.LLM_API_KEY:
        print("\nWARNING: LLM_API_KEY environment variable not set.")
        print("Skipping live LLM test. Create/check .env file or set environment variables.")
    elif not settings.LLM_API_URL and (not settings.LLM_API_ENDPOINT or not settings.MODEL_ID):
        print("\nWARNING: You must provide either LLM_API_URL or both LLM_API_ENDPOINT and MODEL_ID.")
        print("Skipping live LLM test. Create/check .env file or set environment variables.")
    else:
        # Determine which API URL to use for the test
        api_url = settings.LLM_API_URL
        if not api_url and settings.LLM_API_ENDPOINT and settings.MODEL_ID:
            # Check if we're using Gemini 2.0 models which use a different API version
            if "2.0" in settings.MODEL_ID:
                # Gemini 2.0 models use v1beta
                api_url = f"{settings.LLM_API_ENDPOINT.rstrip('/')}/v1beta/models/{settings.MODEL_ID}:generateContent"
            else:
                # Gemini 1.0 models use v1
                api_url = f"{settings.LLM_API_ENDPOINT.rstrip('/')}/v1/models/{settings.MODEL_ID}:generateContent"

        print(f"--- Testing LLM Utility with API URL: {api_url} ---")
        print(f"--- Model ID: {settings.MODEL_ID or 'Not specified directly'} ---")
        sample_html = """
        <div class="contact-info">
            <p>John Doe</p>
            <span>123 Main St<br/>Anytown, CA 90210</span>
            <p>Phone: 555-1234</p>
        </div>
        """
        try:
            address_data = LLM_Utility.extract_address_from_html(sample_html)
            if address_data:
                print("Extracted Address Data:")
                print(json.dumps(address_data, indent=2))
            else:
                # This case might indicate an issue if an exception wasn't raised
                print("Failed to extract address data (returned None). Check logs.")
        except (LLMAPIError, LLMContentError, LLMJsonParsingError) as e:
            print(f"An error occurred during LLM extraction: {e}")
        except (KeyError, AttributeError, ConnectionError, TimeoutError) as e:
            print(f"An unexpected error occurred during test: {e}")
