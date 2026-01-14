# =============================================================================
# Local File Organizer - LLM Classifier Component
# =============================================================================
"""
LLM Classifier: Semantic file classification using Ollama.

The LLM Classifier is used for files that don't match deterministic rules:
1. Builds classification prompts with file content
2. Sends requests to local Ollama server
3. Parses and validates JSON responses
4. Retries on invalid responses with correction prompts
5. Routes low-confidence items to inbox

Model: qwen2.5:14b (configurable)
Response Format: Strict JSON with validation

Safety Features:
- Local execution (no cloud API calls)
- Validation of all LLM outputs
- Retry logic with correction prompts
- Fallback to inbox for uncertain cases
"""
import json
import re
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import asyncio
from concurrent.futures import ThreadPoolExecutor

import requests
import httpx

from src.organizer.models import FileRecord, Classification, VALID_CATEGORIES
from ..settings_manager import get_settings_manager
from .gpu_detector import get_detector


# Configure logging
logger = logging.getLogger(__name__)


# =============================================================================
# Constants
# =============================================================================

DEFAULT_MODEL = "qwen2.5:14b"
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT = 60
DEFAULT_MAX_RETRIES = 3
DEFAULT_MIN_CONFIDENCE = 85


# =============================================================================
# Prompt Templates
# =============================================================================

CLASSIFICATION_PROMPT_TEMPLATE = """You are a file organization assistant. Analyze the following file and classify it into the appropriate category.

## File Information
- **Filename**: {filename}
- **Extension**: {extension}
- **Size**: {size} bytes
- **Modified Date**: {mtime}

## Content Excerpt
{content_excerpt}

## Valid Categories
{categories}

## Instructions
1. Analyze the file content and metadata
2. Choose the most appropriate category from the list above
3. Provide a confidence score (0-100) based on how certain you are
4. If confidence is below 85, use "90_Inbox_Organizar"

## Required JSON Response Format
Respond ONLY with a valid JSON object in this exact format:
```json
{{
    "categoria": "one of the valid categories above",
    "subcategoria": "specific subcategory within the category",
    "assunto": "brief description of the document subject (max 50 chars)",
    "ano": YYYY,
    "nome_sugerido": "YYYY-MM-DD__Categoria__Assunto.ext",
    "confianca": 0-100,
    "racional": "Brief explanation of why this classification was chosen"
}}
```

Respond with valid JSON only. No additional text."""

CORRECTION_PROMPT_TEMPLATE = """Your previous response was invalid. Please try again.

Error: {error}

Remember to respond with ONLY valid JSON in this format:
```json
{{
    "categoria": "one of: {categories}",
    "subcategoria": "string",
    "assunto": "string (max 50 chars)",
    "ano": YYYY (number between 1900-2100),
    "nome_sugerido": "string",
    "confianca": 0-100 (number),
    "racional": "string"
}}
```

Original file: {filename}
Content excerpt: {content_excerpt}

Respond with valid JSON only."""


# =============================================================================
# Helper Functions
# =============================================================================

def build_classification_prompt(record: FileRecord) -> str:
    """
    Build classification prompt for LLM.
    
    Args:
        record: FileRecord to classify
    
    Returns:
        Formatted prompt string
    """
    # Format categories with descriptions
    categories_str = "\n".join([f"- {cat}" for cat in VALID_CATEGORIES])
    
    # Format content excerpt
    content = record.content_excerpt or "(No content extracted)"
    if len(content) > 2000:
        content = content[:2000] + "\n[TRUNCATED]"
    
    return CLASSIFICATION_PROMPT_TEMPLATE.format(
        filename=record.path.name,
        extension=record.extension,
        size=record.size,
        mtime=record.mtime.strftime("%Y-%m-%d %H:%M:%S"),
        content_excerpt=content,
        categories=categories_str,
    )


def build_correction_prompt(
    record: FileRecord,
    error: str
) -> str:
    """
    Build correction prompt after invalid response.
    
    Args:
        record: FileRecord being classified
        error: Error message from validation
    
    Returns:
        Formatted correction prompt
    """
    content = record.content_excerpt or "(No content)"
    if len(content) > 500:
        content = content[:500] + "..."
    
    return CORRECTION_PROMPT_TEMPLATE.format(
        error=error,
        categories=", ".join(VALID_CATEGORIES),
        filename=record.path.name,
        content_excerpt=content,
    )


def parse_llm_response(response: str) -> Optional[Dict]:
    """
    Parse LLM response and extract JSON.
    
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


def validate_classification_json(data: Dict) -> Tuple[bool, List[str]]:
    """
    Validate classification JSON against schema.
    
    Args:
        data: Parsed JSON dict
    
    Returns:
        Tuple of (is_valid, list of error messages)
    """
    errors = []
    
    required_fields = [
        "categoria", "subcategoria", "assunto",
        "ano", "nome_sugerido", "confianca", "racional"
    ]
    
    # Check required fields
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")
    
    if errors:
        return False, errors
    
    # Validate categoria
    if data["categoria"] not in VALID_CATEGORIES:
        errors.append(
            f"Invalid categoria: {data['categoria']}. "
            f"Must be one of: {VALID_CATEGORIES}"
        )
    
    # Validate confianca range
    try:
        confianca = int(data["confianca"])
        if not 0 <= confianca <= 100:
            errors.append(f"Confianca must be 0-100, got: {confianca}")
    except (ValueError, TypeError):
        errors.append(f"Confianca must be a number, got: {data['confianca']}")
    
    # Validate ano range
    try:
        ano = int(data["ano"])
        if not 1900 <= ano <= 2100:
            errors.append(f"Ano must be 1900-2100, got: {ano}")
    except (ValueError, TypeError):
        errors.append(f"Ano must be a number, got: {data['ano']}")
    
    return len(errors) == 0, errors


# =============================================================================
# Ollama Client
# =============================================================================

class OllamaClient:
    """
    HTTP client for Ollama API.
    
    Handles communication with the local Ollama server.
    
    Attributes:
        base_url: Ollama server URL
        model: Model to use for generation
        timeout: Request timeout in seconds
    """
    
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
    ):
        """
        Initialize Ollama client.
        
        Args:
            base_url: Ollama server URL
            model: Model name (e.g., "qwen2.5:14b")
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
    
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
    
    def generate(
        self,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.1,
    ) -> Optional[str]:
        """
        Generate text completion.
        
        Args:
            prompt: Input prompt
            system: Optional system message
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
        
        if system:
            payload["system"] = system
        
        try:
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
        except Exception as e:
            logger.error(f"Ollama request error: {e}")
            return None


# =============================================================================
# LLM Classifier
# =============================================================================

class LLMClassifier:
    """
    Semantic file classifier using Ollama LLM.
    
    Used for files that don't match deterministic rules.
    Validates and retries on invalid responses.
    
    Attributes:
        client: OllamaClient instance
        min_confidence: Minimum confidence threshold
        max_retries: Maximum retry attempts
        stats: Classification statistics
    """
    
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        model: str = DEFAULT_MODEL,
        timeout: int = DEFAULT_TIMEOUT,
        min_confidence: int = DEFAULT_MIN_CONFIDENCE,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backend: str = "ollama",
        **kwargs
    ):
        """
        Initialize LLM classifier with settings from YAML.
        
        Args:
            backend: "ollama", "gemini", or "openai" (from CLI flag)
            model: Override default model from settings
            **kwargs: Additional overrides (batch_size, timeout, etc.)
        """
        self.backend = backend
        settings = get_settings_manager()
        
        # Load backend config from settings.yaml
        backend_config = settings.get_backend_config(backend)
        
        if backend == "ollama":
            # Ollama-specific configuration
            self.base_url = backend_config.get("base_url", "http://localhost:11434")
            self.timeout = backend_config.get("timeout", 45)
            
            # Auto-detect GPU and merge with settings
            gpu_config = self._configure_ollama_gpu(backend_config, kwargs)
            self.batch_size = gpu_config["batch_size"]
            self.max_concurrent = gpu_config["max_concurrent"]
            self.model = model or gpu_config.get("model") or backend_config.get("default_model", "qwen2.5:7b")
            
            logger.info(f"🚀 Ollama: {self.base_url}, model={self.model}, "
                       f"batch={self.batch_size}, concurrent={self.max_concurrent}")
            
            self._verify_ollama()
            
        elif backend == "gemini":
            # Gemini configuration from settings.yaml
            self.model = model or backend_config.get("default_model", "gemini-1.5-flash")
            self.temperature = backend_config.get("temperature", 0.3)
            self.timeout = backend_config.get("timeout", 30)
            self.rate_limit = backend_config.get("rate_limit", 30)
            self.batch_size = kwargs.get("batch_size", 5)
            self.max_concurrent = kwargs.get("max_concurrent", 3)
            
            logger.info(f"☁️ Gemini: model={self.model}, rate_limit={self.rate_limit}/min")
            
        elif backend == "openai":
            # OpenAI configuration from settings.yaml
            self.model = model or backend_config.get("default_model", "gpt-4o-mini")
            self.temperature = backend_config.get("temperature", 0.3)
            self.timeout = backend_config.get("timeout", 30)
            self.organization = backend_config.get("organization")
            self.batch_size = kwargs.get("batch_size", 5)
            self.max_concurrent = kwargs.get("max_concurrent", 3)
            
            logger.info(f"☁️ OpenAI: model={self.model}")
        
        else:
            raise ValueError(f"Unknown backend: {backend}")
    
    def _configure_ollama_gpu(self, backend_config: Dict, overrides: Dict) -> Dict[str, Any]:
        """
        Configure Ollama with GPU detection + settings.yaml + CLI overrides.
        
        Priority: CLI overrides > GPU detection > settings.yaml > defaults
        """
        detector = get_detector()
        
        # Start with GPU detection
        if "gpu_tier" in overrides:
            gpu_config = detector.get_config(tier=overrides["gpu_tier"])
        else:
            gpu_config = detector.auto_configure()
        
        # Apply CLI overrides
        if "batch_size" in overrides:
            gpu_config["batch_size"] = overrides["batch_size"]
        if "max_concurrent" in overrides:
            gpu_config["max_concurrent"] = overrides["max_concurrent"]
        if "model" in overrides:
            gpu_config["model"] = overrides["model"]
        
        return gpu_config

    def classify(self, record: FileRecord) -> Optional[Classification]:
        """
        Classify a FileRecord using LLM.
        
        Args:
            record: FileRecord to classify
        
        Returns:
            Classification if successful, None otherwise
        """
        prompt = build_classification_prompt(record)
        last_error = "Invalid JSON response"
        
        for attempt in range(self.max_retries):
            # Use correction prompt on retries
            if attempt > 0:
                prompt = build_correction_prompt(record, last_error)
                self.stats["retries"] += 1
            
            # Get LLM response
            response = self.client.generate(prompt)
            
            if not response:
                last_error = "No response from LLM"
                continue
            
            # Parse JSON
            data = parse_llm_response(response)
            
            if not data:
                last_error = "Could not parse JSON from response"
                continue
            
            # Validate
            is_valid, errors = validate_classification_json(data)
            
            if not is_valid:
                last_error = "; ".join(errors)
                continue
            
            # Check confidence
            confianca = int(data["confianca"])
            
            if confianca < self.min_confidence:
                self.stats["low_confidence"] += 1
                # Route to inbox or return None
                return None
            
            # Success!
            self.stats["successful"] += 1
            return self._create_classification(record, data)
        
        # All retries exhausted
        self.stats["failed"] += 1
        logger.warning(
            f"Classification failed for {record.path.name} after "
            f"{self.max_retries} attempts: {last_error}"
        )
        return None
    
    async def classify_batch(self, files: List[FileRecord]) -> List[ClassificationResult]:
        """
        🔥 NOVO: Classifica múltiplos arquivos em paralelo para maximizar GPU
        
        Args:
            files: Lista de arquivos a classificar
            
        Returns:
            Lista de resultados (mesma ordem de entrada)
        """
        if not files:
            return []
            
        logger.info(f"Processando batch de {len(files)} arquivos (concorrência: {self.max_concurrent})")
        
        # Cria semáforo para controlar concorrência
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async def classify_with_semaphore(file_record: FileRecord) -> ClassificationResult:
            async with semaphore:
                return await self._classify_single(file_record)
        
        # Processa todos em paralelo (respeitando semáforo)
        tasks = [classify_with_semaphore(f) for f in files]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Converte exceções em resultados de erro
        final_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Erro no arquivo {files[i].path}: {result}")
                final_results.append(self._fallback_result(files[i], str(result)))
            else:
                final_results.append(result)
        
        return final_results

    async def _classify_single(self, file_record: FileRecord) -> ClassificationResult:
        """Classifica um único arquivo (método interno)"""
        if self.backend == "ollama":
            return await self._classify_ollama(file_record)
        elif self.backend == "gemini":
            return await self._classify_gemini(file_record)
        elif self.backend == "openai":
            return await self._classify_openai(file_record)
        else:
            raise ValueError(f"Backend desconhecido: {self.backend}")

    async def _classify_ollama(self, file_record: FileRecord) -> ClassificationResult:
        """Classifica via Ollama com retry e timeout"""
        prompt = self._build_prompt(file_record)
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(3):  # 3 tentativas
                try:
                    response = await client.post(
                        f"{self.base_url}/api/generate",
                        json={
                            "model": self.model,
                            "prompt": prompt,
                            "format": "json",  # Força JSON puro
                            "stream": False,
                            "options": {
                                "temperature": 0.3,  # Mais determinístico
                                "num_predict": 512,
                                # 🔥 GPU optimization
                                "num_gpu": -1,  # Usa todas GPUs disponíveis
                                "num_thread": 4,  # Threads CPU para pré/pós-processamento
                            }
                        }
                    )
                    response.raise_for_status()
                    
                    result_text = response.json()["response"]
                    classification = self._parse_json_response(result_text)
                    
                    return ClassificationResult(
                        categoria=classification["categoria"],
                        subcategoria=classification.get("subcategoria", ""),
                        assunto=classification.get("assunto", ""),
                        ano=classification.get("ano", ""),
                        nome_sugerido=classification.get("nome_sugerido", ""),
                        confianca=classification.get("confianca", 0),
                        racional=classification.get("racional", "")
                    )
                    
                except (httpx.TimeoutException, httpx.HTTPError) as e:
                    if attempt < 2:
                        logger.warning(f"Tentativa {attempt+1} falhou: {e}, retry em 2s...")
                        await asyncio.sleep(2)
                    else:
                        raise
