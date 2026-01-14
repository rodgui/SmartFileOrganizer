"""
Ollama Analyzer - Local AI analysis using Ollama

This module provides document analysis using local Ollama models,
offering privacy-focused, offline-capable AI processing.
"""

import json
import logging
import requests
from typing import Optional, Dict, List

logger = logging.getLogger("AIDocumentOrganizer")


class OllamaAnalyzer:
    """
    Class for analyzing document content using local Ollama server.
    
    This provides a privacy-first approach where all AI processing
    happens locally without sending data to cloud services.
    """
    
    DEFAULT_URL = "http://localhost:11434"
    DEFAULT_MODEL = "qwen2.5:14b"
    DEFAULT_TIMEOUT = 60
    
    def __init__(self, settings_manager=None):
        """
        Initialize Ollama analyzer.
        
        Args:
            settings_manager: Optional settings manager for configuration
        """
        self.settings_manager = settings_manager
        
        # Get URL and model from settings
        self.base_url = self.DEFAULT_URL
        self.model = self.DEFAULT_MODEL
        self.timeout = self.DEFAULT_TIMEOUT
        
        if settings_manager:
            self.base_url = settings_manager.get_setting(
                "ai_service.ollama_url", self.DEFAULT_URL
            )
            self.model = settings_manager.get_setting(
                "ai_service.ollama_model", self.DEFAULT_MODEL
            )
        
        # Clean URL
        self.base_url = self.base_url.rstrip("/")
        
        # Define available models (common ones)
        self.available_models = [
            "qwen2.5:14b",
            "qwen2.5:7b",
            "qwen2.5:3b",
            "llama3.2",
            "llama3.1:8b",
            "llama3.1:70b",
            "mistral",
            "mixtral",
            "codellama",
            "phi3",
            "gemma2",
        ]
        
        logger.info(f"Ollama analyzer initialized: {self.base_url} with model {self.model}")
    
    def get_available_models(self) -> List[str]:
        """
        Get list of available Ollama models.
        
        Returns:
            List of model names
        """
        # Try to get models from server
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            if response.status_code == 200:
                data = response.json()
                models = [m["name"] for m in data.get("models", [])]
                if models:
                    return models
        except Exception as e:
            logger.warning(f"Could not fetch models from Ollama: {e}")
        
        return self.available_models
    
    def set_model(self, model_name: str) -> bool:
        """
        Set the model to use for analysis.
        
        Args:
            model_name: Name of the model to use
            
        Returns:
            True if successful, False otherwise
        """
        try:
            self.model = model_name
            
            # Save to settings if available
            if self.settings_manager:
                self.settings_manager.set_setting("ai_service.ollama_model", model_name)
                self.settings_manager.save_settings()
            
            logger.info(f"Switched to Ollama model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Error setting Ollama model: {e}")
            return False
    
    def health_check(self) -> bool:
        """
        Check if Ollama server is available.
        
        Returns:
            True if server is healthy
        """
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False
    
    def analyze_content(self, text: str, file_type: str) -> Dict:
        """
        Analyze document content using Ollama.
        
        Args:
            text: The document text content
            file_type: The type of document (CSV, Excel, HTML, etc.)
            
        Returns:
            Dictionary with analysis results
        """
        # Truncate text if too long
        max_text_length = 8000  # Conservative limit for local models
        truncated_text = text[:max_text_length]
        if len(text) > max_text_length:
            truncated_text += f"\n\n[Content truncated. Original length: {len(text)} characters]"
        
        try:
            analysis = self._get_content_analysis(truncated_text, file_type)
            return analysis
        except Exception as e:
            logger.error(f"Error in Ollama analysis: {str(e)}")
            return {
                "category": "Unclassified",
                "keywords": ["document"],
                "summary": "Error analyzing document content with Ollama."
            }
    
    def _get_content_analysis(self, text: str, file_type: str) -> Dict:
        """
        Get AI analysis of document content using Ollama.
        
        Args:
            text: The document text
            file_type: The type of document
            
        Returns:
            Dictionary with analysis results
        """
        prompt = f"""You are a document analyzer. Analyze the following {file_type} document and provide:
1. A category for document organization (choose the most appropriate)
2. 3-5 keywords that represent the main topics
3. A brief summary (max 2-3 sentences)

Document content:
{text}

Return ONLY a valid JSON object with this exact structure:
{{
    "category": "Category name",
    "keywords": ["keyword1", "keyword2", "keyword3"],
    "summary": "Brief summary of the content"
}}

Respond with ONLY valid JSON. No additional text."""

        max_retries = 3
        for attempt in range(max_retries):
            try:
                response_text = self._generate(prompt)
                
                if not response_text:
                    logger.warning(f"Empty response from Ollama (attempt {attempt + 1})")
                    continue
                
                logger.info(f"Ollama response received: {response_text[:100]}...")
                
                # Parse JSON response
                result = self._parse_json_response(response_text)
                
                if result and all(k in result for k in ["category", "keywords", "summary"]):
                    return result
                
                logger.warning(f"Invalid response format (attempt {attempt + 1})")
                
            except Exception as e:
                logger.error(f"Ollama analysis error (attempt {attempt + 1}): {e}")
        
        # Return default if all attempts fail
        return {
            "category": "Unclassified",
            "keywords": ["document"],
            "summary": "Could not analyze document."
        }
    
    def _generate(self, prompt: str, temperature: float = 0.1) -> Optional[str]:
        """
        Generate text completion using Ollama.
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature (lower = more deterministic)
            
        Returns:
            Generated text or None on error
        """
        payload = {
            "model": self.model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": temperature,
            }
        }
        
        try:
            logger.info(f"Sending request to Ollama: {self.base_url}/api/generate")
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=self.timeout,
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get("response", "")
            else:
                logger.error(
                    f"Ollama generate failed: {response.status_code} - {response.text}"
                )
                return None
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Cannot connect to Ollama at {self.base_url}: {e}")
            return None
        except Exception as e:
            logger.error(f"Ollama request error: {e}")
            return None
    
    def _parse_json_response(self, response: str) -> Optional[Dict]:
        """
        Parse JSON from LLM response.
        
        Handles:
        - Pure JSON responses
        - JSON wrapped in markdown code blocks
        - JSON with surrounding text
        
        Args:
            response: Raw LLM response string
            
        Returns:
            Parsed JSON dict or None if parsing fails
        """
        if not response or not response.strip():
            return None
        
        response = response.strip()
        
        # Try direct JSON parse first
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try extracting from markdown code block
        import re
        code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", response, re.DOTALL)
        if code_block_match:
            try:
                return json.loads(code_block_match.group(1).strip())
            except json.JSONDecodeError:
                pass
        
        # Try finding JSON object in text
        json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        # Try finding nested JSON (with potential nested objects)
        brace_count = 0
        start_idx = None
        for i, char in enumerate(response):
            if char == "{":
                if start_idx is None:
                    start_idx = i
                brace_count += 1
            elif char == "}":
                brace_count -= 1
                if brace_count == 0 and start_idx is not None:
                    try:
                        return json.loads(response[start_idx:i + 1])
                    except json.JSONDecodeError:
                        start_idx = None
        
        return None
    
    def analyze_image(self, image_path: str) -> Dict:
        """
        Analyze an image file.
        
        Note: Image analysis requires a multimodal model like llava.
        
        Args:
            image_path: Path to the image file
            
        Returns:
            Dictionary with analysis results
        """
        # Basic implementation - most Ollama models don't support vision
        return {
            "description": "Image analysis requires a multimodal model",
            "objects": [],
            "text_content": "",
            "category": "Images"
        }
