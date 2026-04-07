"""
LLM Client - handles OpenAI API calls
"""
from typing import Optional, Dict, Any
import re
from openai import OpenAI
from shared.logger import get_logger
from config.settings import config

logger = get_logger(__name__)


class LLMClient:
    """
    Client for OpenAI LLM API calls.
    Wraps OpenAI client with error handling and logging.
    """
    
    def __init__(
        self, 
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2000
    ):
        """
        Initialize LLM client
        
        Args:
            api_key: OpenAI API key (uses config if not provided)
            model: Model name (uses config if not provided)
            temperature: Sampling temperature
            max_tokens: Maximum tokens in response
        """
        self.api_key = api_key or config.llm.api_key
        self.model = model or config.llm.model
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        if not self.api_key:
            logger.error("OpenAI API key not found in OPENAI_API_KEY")
            raise ValueError("OPENAI_API_KEY environment variable not set")
        
        try:
            self.client = OpenAI(api_key=self.api_key)
        except TypeError:
            # Fallback for different OpenAI versions
            self.client = OpenAI(api_key=self.api_key)
        
        logger.info(f"LLM Client initialized with model: {self.model}")
    
    def invoke(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Call OpenAI API with system and user prompts
        
        Args:
            system_prompt: System role message
            user_prompt: User message
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            Response text from LLM
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            logger.debug(f"Calling LLM: {self.model}")
            logger.debug(f"System prompt: {system_prompt[:100]}...")
            logger.debug(f"User prompt: {user_prompt[:100]}...")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temp,
                max_tokens=tokens
            )
            
            result = response.choices[0].message.content
            logger.info(f"LLM response received ({len(result)} chars)")
            return result
            
        except Exception as e:
            logger.error(f"LLM API call failed: {str(e)}")
            raise
    
    def invoke_json(
        self,
        system_prompt: str,
        user_prompt: str,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Call OpenAI API with JSON output format
        Useful for structured outputs
        
        Args:
            system_prompt: System role message
            user_prompt: User message
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            
        Returns:
            Parsed JSON response
        """
        import json
        
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        try:
            logger.debug(f"Calling LLM (JSON mode): {self.model}")

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=temp,
                max_tokens=tokens,
                response_format={"type": "json_object"}
            )

            result_text = response.choices[0].message.content
            result = json.loads(result_text)
            logger.info("LLM JSON response received")
            return result

        except Exception as e:
            error_text = str(e)

            if "response_format" in error_text and "not supported" in error_text:
                logger.warning(
                    "Model %s does not support response_format=json_object. Falling back to text JSON parsing.",
                    self.model,
                )
                fallback_user_prompt = (
                    f"{user_prompt}\n\n"
                    "IMPORTANT: Return ONLY a valid JSON object. "
                    "Do not include markdown code fences or extra commentary."
                )
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": fallback_user_prompt}
                    ],
                    temperature=temp,
                    max_tokens=tokens,
                )
                result_text = response.choices[0].message.content
                return self._parse_json_text(result_text)

            logger.error(f"LLM API call failed: {error_text}")
            raise

    def _parse_json_text(self, text: str) -> Dict[str, Any]:
        """Parse JSON object from plain model output, tolerating fenced blocks."""
        import json

        raw = (text or "").strip()
        try:
            result = json.loads(raw)
            if not isinstance(result, dict):
                raise ValueError("JSON response must be an object")
            logger.info("LLM JSON response parsed from text mode")
            return result
        except Exception:
            pass

        match = re.search(r"\{[\s\S]*\}", raw)
        if not match:
            logger.error("Failed to parse JSON response: no JSON object found")
            raise ValueError("No JSON object found in model response")

        try:
            result = json.loads(match.group(0))
        except Exception as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            raise

        if not isinstance(result, dict):
            raise ValueError("JSON response must be an object")

        logger.info("LLM JSON response parsed from extracted text")
        return result
    
    def test_connection(self) -> bool:
        """
        Test if LLM connection is working
        
        Returns:
            True if connection successful
        """
        try:
            logger.info("Testing LLM connection...")
            response = self.invoke(
                system_prompt="You are a helpful assistant.",
                user_prompt="Say 'LLM connection successful' in exactly those words.",
                max_tokens=20
            )
            logger.info(f"Connection test response: {response}")
            return "successful" in response.lower()
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return False
