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
        if not config.LLM_API_ENDPOINT or not config.LLM_API_KEY:
            logger.warning("LLM_API_ENDPOINT or LLM_API_KEY is not configured. Skipping LLM extraction.")
            return None

        prompt = cls._construct_prompt(html_snippet)
        headers = {
            "Authorization": f"Bearer {config.LLM_API_KEY}",
            "Content-Type": "application/json",
        }
        # This payload structure is hypothetical and depends on the specific LLM API
        payload = {
            "prompt": prompt,
            "max_tokens": 150,  # Adjust as needed
            "temperature": 0.2,  # Adjust for desired creativity/determinism
            # Add other parameters required by the specific LLM API
        }

        last_exception: Optional[Exception] = LLMAPIError("LLM request failed after all retries.")  # Initialize with a default error

        for attempt in range(config.LLM_MAX_RETRIES):
            try:
                response = requests.post(
                    config.LLM_API_ENDPOINT,
                    headers=headers,
                    json=payload,
                    timeout=config.LLM_REQUEST_TIMEOUT_SECONDS,
                )
                response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)

                # --- LLM Response Handling (Highly dependent on the specific LLM API) ---
                # 1. Check for LLM-specific errors (e.g., content flags)
                # This part needs to be adapted based on the actual API response structure
                response_data = response.json()
                if response_data.get("error"):  # Hypothetical error field
                    error_msg = f"LLM API error: {response_data['error']}"
                    logger.error(error_msg)
                    # Don't retry on definitive API errors returned in the response body
                    raise LLMContentError(error_msg)
                if response_data.get("blocked", False):  # Hypothetical content flag
                    logger.warning("LLM response blocked due to content moderation.")
                    # Don't retry on content moderation blocks
                    raise LLMContentError("LLM response blocked due to content moderation.")

                # 2. Extract the actual text content containing the JSON
                # This is also hypothetical - adjust based on the API
                llm_output_text = response_data.get("choices", [{}])[0].get("text", "").strip()
                if not llm_output_text:
                    llm_output_text = response_data.get("result", "").strip()  # Alternative structure
                if not llm_output_text:
                    logger.error(f"Could not extract text from LLM response: {response_data}")
                    # Don't retry if the response structure is wrong
                    raise LLMContentError("Could not extract text from LLM response.")

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
    # 2. Add your LLM endpoint and key:
    #    LLM_API_ENDPOINT="YOUR_ENDPOINT_HERE"
    #    LLM_API_KEY="YOUR_API_KEY_HERE"
    # 3. Or set environment variables:
    #    export LLM_API_ENDPOINT="YOUR_ENDPOINT"
    #    export LLM_API_KEY="YOUR_KEY"

    # For local development, you might want to use dotenv:
    # from dotenv import load_dotenv
    # load_dotenv()

    # Use the same settings mechanism as the rest of the application
    settings = get_settings()

    if not settings.LLM_API_ENDPOINT or not settings.LLM_API_KEY:
        print("\nWARNING: LLM_API_ENDPOINT and LLM_API_KEY environment variables not set.")
        print("Skipping live LLM test. Create/check .env file or set environment variables.")
    else:
        print(f"--- Testing LLM Utility with endpoint: {settings.LLM_API_ENDPOINT} ---")
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
