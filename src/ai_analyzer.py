import os
import json
import time
import random
import logging

logger = logging.getLogger("AIDocumentOrganizer")

# Try new SDK first, fall back to legacy
try:
    from google import genai
    from google.genai import types
    USING_NEW_SDK = True
    genai_legacy = None  # Not using legacy SDK
except ImportError:
    try:
        import google.generativeai as genai_legacy
        USING_NEW_SDK = False
        genai = None  # Not using new SDK
        types = None
        logger.warning("Using legacy google.generativeai SDK. Consider upgrading to google-genai.")
    except ImportError:
        genai_legacy = None
        genai = None
        types = None
        USING_NEW_SDK = False
        logger.error("No Google AI SDK found. Install google-genai package.")


class AIAnalyzer:
    """
    Class for analyzing document content using Google Gemini API
    Supports both new google-genai SDK and legacy google.generativeai
    """

    def __init__(self, settings_manager=None):
        # Get API key from environment variable or settings
        # New SDK uses GEMINI_API_KEY, legacy uses GOOGLE_API_KEY
        api_key = os.environ.get("GEMINI_API_KEY") or os.environ.get("GOOGLE_API_KEY", "")
        if not api_key and settings_manager:
            api_key = settings_manager.get_setting("ai_service.google_api_key", "")
            if api_key:
                os.environ["GEMINI_API_KEY"] = api_key
                os.environ["GOOGLE_API_KEY"] = api_key

        if not api_key:
            logger.warning("GEMINI_API_KEY/GOOGLE_API_KEY environment variable not set.")

        # Rate limiting settings
        self.requests_per_minute = 30
        if settings_manager:
            self.requests_per_minute = settings_manager.get_setting(
                "ai_service.requests_per_minute", 30)

        self.min_request_interval = 60.0 / self.requests_per_minute
        self.last_request_time = 0
        self.max_retries = 5
        if settings_manager:
            self.max_retries = settings_manager.get_setting("ai_service.max_retries", 5)

        self.base_delay = 2
        self.settings_manager = settings_manager
        self.client = None
        self.model_name = None
        self.available_models = []

        if USING_NEW_SDK:
            self._init_new_sdk(api_key, settings_manager)
        elif genai_legacy:
            self._init_legacy_sdk(api_key, settings_manager)
        else:
            logger.error("No Google AI SDK available")
            self.available_models = []
            self.model_name = None

    def _init_new_sdk(self, api_key, settings_manager):
        """Initialize the new google-genai SDK"""
        try:
            # Create client (uses GEMINI_API_KEY env var or explicit key)
            self.client = genai.Client(api_key=api_key) if api_key else genai.Client()
            
            # Get available models
            try:
                self.available_models = [m.name for m in self.client.models.list()]
                logger.info(f"Available Gemini models: {self.available_models}")
            except Exception as e:
                logger.warning(f"Could not list models: {e}")
                self.available_models = ["gemini-2.0-flash", "gemini-1.5-flash", "gemini-1.5-pro"]

            # Get the selected model from settings if available
            selected_model = None
            if settings_manager:
                selected_model = settings_manager.get_selected_model("google")

            # Check if the selected model is available
            if selected_model and selected_model in self.available_models:
                self.model_name = selected_model
                logger.info(f"Using selected model from settings: {self.model_name}")
            else:
                # Find the most suitable model
                preferred_models = [
                    'gemini-2.0-flash',
                    'models/gemini-2.0-flash',
                    'gemini-1.5-flash',
                    'models/gemini-1.5-flash',
                    'gemini-1.5-pro',
                    'models/gemini-1.5-pro',
                ]

                self.model_name = None
                for preferred in preferred_models:
                    if preferred in self.available_models:
                        self.model_name = preferred
                        break

                # If none of our preferred models are available, use first with "gemini"
                if not self.model_name:
                    for m in self.available_models:
                        if 'gemini' in m.lower():
                            self.model_name = m
                            break

                # Fallback
                if not self.model_name:
                    self.model_name = "gemini-2.0-flash"

                # Save the selected model to settings
                if settings_manager and self.model_name:
                    settings_manager.set_selected_model("google", self.model_name)

            logger.info(f"Using model: {self.model_name}")

        except Exception as e:
            logger.error(f"Error initializing new SDK: {e}")
            self.model_name = "gemini-2.0-flash"
            self.available_models = [self.model_name]

    def _init_legacy_sdk(self, api_key, settings_manager):
        """Initialize the legacy google.generativeai SDK"""
        try:
            genai_legacy.configure(api_key=api_key)

            # Get available models
            try:
                self.available_models = [m.name for m in genai_legacy.list_models()]
                logger.info(f"Available Gemini models (legacy): {self.available_models}")
            except Exception as e:
                logger.warning(f"Could not list models: {e}")
                self.available_models = ["models/gemini-1.5-flash", "models/gemini-1.5-pro"]

            # Get the selected model from settings if available
            selected_model = None
            if settings_manager:
                selected_model = settings_manager.get_selected_model("google")

            if selected_model and selected_model in self.available_models:
                model_name = selected_model
                logger.info(f"Using selected model from settings: {model_name}")
            else:
                preferred_models = [
                    'models/gemini-2.0-flash',
                    'models/gemini-1.5-flash',
                    'models/gemini-1.5-pro',
                    'models/gemini-1.0-pro',
                    'gemini-pro'
                ]

                model_name = None
                for preferred in preferred_models:
                    if preferred in self.available_models:
                        model_name = preferred
                        break

                if not model_name:
                    for m in self.available_models:
                        if 'gemini' in m.lower():
                            model_name = m
                            break

                if not model_name and self.available_models:
                    model_name = self.available_models[0]

                if not model_name:
                    model_name = "models/gemini-1.5-flash"

                if settings_manager and model_name:
                    settings_manager.set_selected_model("google", model_name)

            logger.info(f"Using model (legacy): {model_name}")
            self.model = genai_legacy.GenerativeModel(model_name)
            self.model_name = model_name

        except Exception as e:
            logger.error(f"Error initializing legacy SDK: {e}")
            fallback_model = "models/gemini-1.5-pro"
            logger.warning(f"Falling back to {fallback_model} model")
            self.model = genai_legacy.GenerativeModel(fallback_model)
            self.model_name = fallback_model
            self.available_models = [fallback_model]

    def get_available_models(self):
        """Get list of available Gemini models"""
        return self.available_models

    def set_model(self, model_name):
        """
        Set the model to use for analysis

        Args:
            model_name: Name of the model to use

        Returns:
            True if successful, False otherwise
        """
        try:
            if model_name in self.available_models:
                self.model_name = model_name
                
                if not USING_NEW_SDK and genai_legacy:
                    self.model = genai_legacy.GenerativeModel(model_name)

                # Save to settings if available
                if self.settings_manager:
                    self.settings_manager.set_selected_model("google", model_name)

                logger.info(f"Switched to model: {model_name}")
                return True
            else:
                logger.warning(f"Model {model_name} not available")
                return False
        except Exception as e:
            logger.error(f"Error setting model: {e}")
            return False

    def _generate_content(self, prompt, temperature=0.2, max_output_tokens=800):
        """
        Generate content using the appropriate SDK
        
        Args:
            prompt: The prompt to send
            temperature: Generation temperature
            max_output_tokens: Maximum output tokens
            
        Returns:
            Response text
        """
        if USING_NEW_SDK and self.client:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=temperature,
                    max_output_tokens=max_output_tokens,
                )
            )
            return response.text
        elif genai_legacy:
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_output_tokens,
                }
            )
            if hasattr(response, 'text'):
                return response.text
            else:
                return response.candidates[0].content.parts[0].text
        else:
            raise RuntimeError("No Google AI SDK available")

    def analyze_content(self, text, file_type):
        """
        Analyze document content using AI

        Args:
            text: The document text content
            file_type: The type of document (CSV, Excel, HTML, etc.)

        Returns:
            Dictionary with analysis results
        """
        max_text_length = 30000
        truncated_text = text[:max_text_length]
        if len(text) > max_text_length:
            truncated_text += f"\n\n[Content truncated. Original length: {len(text)} characters]"

        try:
            analysis = self._get_content_analysis(truncated_text, file_type)
            return analysis
        except Exception as e:
            logger.error(f"Error in AI analysis: {str(e)}")
            return {
                "category": "Unclassified",
                "keywords": ["document"],
                "summary": "Error analyzing document content."
            }

    def _get_content_analysis(self, text, file_type):
        """
        Get AI analysis of document content using Google Gemini

        Args:
            text: The document text
            file_type: The type of document

        Returns:
            Dictionary with analysis results
        """
        prompt = f"""
        Please analyze the following {file_type} document content and provide:
        1. A category for document organization (choose the most specific appropriate category)
        2. 3-5 keywords that represent the main topics in the document
        3. A brief summary of the document content (max 2-3 sentences)
        4. The primary theme or subject of the document (1-2 words)

        Content:
        {text}

        Return your analysis in JSON format with the following structure:
        {{
            "category": "Category name",
            "keywords": ["keyword1", "keyword2", "keyword3"],
            "summary": "Brief summary of the content",
            "theme": "Primary theme"
        }}

        Make sure to return ONLY valid JSON without any additional text or explanation.
        """

        for attempt in range(self.max_retries):
            try:
                self._apply_rate_limit()

                response_text = self._generate_content(prompt, temperature=0.2, max_output_tokens=800)

                logger.info(f"AI response received: {response_text[:100]}...")

                # Clean up response
                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]

                result = json.loads(response_text)

                if not all(k in result for k in ["category", "keywords", "summary"]):
                    raise ValueError("Missing required fields in AI response")

                if "theme" not in result and "keywords" in result and result["keywords"]:
                    result["theme"] = result["keywords"][0]

                return result

            except Exception as e:
                error_message = str(e).lower()

                if "429" in error_message or "resource exhausted" in error_message or "quota" in error_message:
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt) + random.uniform(0, 1)
                        logger.warning(
                            f"Rate limit exceeded (429). Retrying in {delay:.2f} seconds (attempt {attempt+1}/{self.max_retries})")
                        time.sleep(delay)
                    else:
                        logger.error("Rate limit exceeded (429). Max retries reached.")
                        raise Exception("AI analysis failed: Rate limit exceeded (429)")
                else:
                    logger.error(f"AI analysis exception: {e}")
                    raise Exception(f"AI analysis failed: {str(e)}")

        raise Exception("AI analysis failed after multiple retries")

    def _apply_rate_limit(self):
        """Apply rate limiting to avoid 429 errors"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time

        if time_since_last_request < self.min_request_interval:
            sleep_time = self.min_request_interval - time_since_last_request
            logger.debug(f"Rate limiting: Sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def find_similar_documents(self, target_doc, document_list, max_results=5):
        """
        Find documents similar to the target document

        Args:
            target_doc: Target document info dictionary
            document_list: List of document info dictionaries to compare against
            max_results: Maximum number of similar documents to return

        Returns:
            List of similar document dictionaries with similarity scores
        """
        if not target_doc or not document_list:
            return []

        target_keywords = set(target_doc.get("keywords", []))
        target_category = target_doc.get("category", "").lower()
        target_theme = target_doc.get("theme", "").lower()
        target_summary = target_doc.get("summary", "")
        target_filename = target_doc.get("filename", "")

        similarity_scores = []

        for doc in document_list:
            if doc.get("filename") == target_filename and doc.get("path") == target_doc.get("path"):
                continue

            doc_keywords = set(doc.get("keywords", []))
            doc_category = doc.get("category", "").lower()
            doc_theme = doc.get("theme", "").lower()
            doc_filename = doc.get("filename", "")

            score = 0
            relationship_factors = []

            if target_keywords and doc_keywords:
                matching_keywords = target_keywords.intersection(doc_keywords)
                keyword_overlap = len(matching_keywords)
                if keyword_overlap > 0:
                    keyword_points = min(6, keyword_overlap * 2)
                    score += keyword_points

                    if keyword_overlap == 1:
                        relationship_factors.append(f"shared keyword '{list(matching_keywords)[0]}'")
                    else:
                        relationship_factors.append(f"{keyword_overlap} shared keywords")

            if target_category and doc_category:
                if target_category == doc_category:
                    score += 3
                    relationship_factors.append("same category")
                elif target_category in doc_category or doc_category in target_category:
                    score += 1
                    relationship_factors.append("related category")

            if target_theme and doc_theme:
                if target_theme == doc_theme:
                    score += 3
                    relationship_factors.append("same theme")
                elif target_theme in doc_theme or doc_theme in target_theme:
                    score += 1
                    relationship_factors.append("related theme")

            target_ext = os.path.splitext(target_filename)[1].lower() if target_filename else ""
            doc_ext = os.path.splitext(doc_filename)[1].lower() if doc_filename else ""
            if target_ext and doc_ext and target_ext == doc_ext:
                score += 2
                relationship_factors.append(f"same file type ({target_ext})")

            relationship_explanation = ""
            if relationship_factors:
                relationship_explanation = f"Documents have {' and '.join(relationship_factors)}"

            relationship_strength = "low"
            if score >= 6:
                relationship_strength = "high"
            elif score >= 3:
                relationship_strength = "medium"

            if score > 0:
                similarity_scores.append((doc, score, relationship_explanation, relationship_strength))

        similarity_scores.sort(key=lambda x: x[1], reverse=True)

        result = []
        for doc, score, explanation, strength in similarity_scores[:max_results]:
            doc_copy = doc.copy()
            doc_copy["similarity_score"] = score
            doc_copy["relationship_explanation"] = explanation
            doc_copy["relationship_strength"] = strength
            result.append(doc_copy)

        return result

    def find_related_content(self, target_doc, document_list, max_results=5):
        """
        Find documents related to the target document using AI comparison

        Args:
            target_doc: Target document info dictionary with content analysis
            document_list: List of document info dictionaries to compare against
            max_results: Maximum number of related documents to return

        Returns:
            Dictionary with relationship information and related documents
        """
        similar_docs = self.find_similar_documents(target_doc, document_list, max_results)

        high_quality_matches = sum(1 for doc in similar_docs if doc.get("similarity_score", 0) >= 5)

        if high_quality_matches >= min(2, max_results):
            return {
                "related_documents": similar_docs,
                "relationship_type": "content_similarity",
                "relationship_strength": "high" if similar_docs and similar_docs[0].get("similarity_score", 0) >= 6 else "medium"
            }

        target_summary = target_doc.get("summary", "")
        target_category = target_doc.get("category", "")
        target_filename = target_doc.get("filename", "")
        target_keywords = target_doc.get("keywords", [])

        if isinstance(target_keywords, list):
            target_keywords = ", ".join(target_keywords)

        if not target_summary:
            return {
                "related_documents": similar_docs,
                "relationship_type": "keyword_match",
                "relationship_strength": "medium" if similar_docs else "low"
            }

        doc_info_list = []
        for doc in document_list:
            if doc.get("filename") == target_filename:
                continue

            if not doc.get("summary"):
                continue

            doc_info = {
                "id": len(doc_info_list),
                "filename": doc.get("filename", ""),
                "category": doc.get("category", ""),
                "summary": doc.get("summary", ""),
                "keywords": doc.get("keywords", [])
            }

            if isinstance(doc_info["keywords"], list):
                doc_info["keywords"] = ", ".join(doc_info["keywords"])

            doc_info_list.append(doc_info)

            if len(doc_info_list) >= 15:
                break

        if not doc_info_list:
            return {
                "related_documents": similar_docs,
                "relationship_type": "keyword_match",
                "relationship_strength": "medium" if similar_docs else "low"
            }

        try:
            docs_text = "\n\n".join([
                f"Document {doc['id']}: {doc['filename']}\n"
                f"Category: {doc['category']}\n"
                f"Keywords: {doc['keywords']}\n"
                f"Summary: {doc['summary']}"
                for doc in doc_info_list
            ])

            prompt = f"""
            Analyze the relationship between the target document and the collection of other documents.
            Look for contextual connections, complementary information, sequential relationships,
            and topical relevance beyond simple keyword matching.

            Target Document: {target_filename}
            Category: {target_category}
            Keywords: {target_keywords}
            Summary: {target_summary}

            Other documents in the collection:
            {docs_text}

            Based on deep content analysis, identify up to {max_results} documents from the collection
            that are most meaningfully related to the target document. Consider:
            - Documents that complement or extend the target's information
            - Documents that represent previous/next steps in a process
            - Documents that provide context or background for the target
            - Documents covering related aspects of the same topic

            For each related document:
            1. The document ID
            2. The relationship strength (high, medium, or low)
            3. The relationship type (e.g., "complementary", "prerequisite", "extension", "contextual", etc.)
            4. A specific explanation of how the documents relate (1-2 sentences)

            Return your analysis in JSON format:
            {{
                "related_documents": [
                    {{
                        "id": document_id,
                        "relationship_strength": "high|medium|low",
                        "relationship_type": "relationship type",
                        "relationship_explanation": "Specific explanation of the relationship"
                    }},
                    ...
                ]
            }}

            Provide ONLY the JSON object, no other text.
            """

            try:
                response_text = self._generate_content(prompt, temperature=0.4, max_output_tokens=1200)

                response_text = response_text.strip()
                if response_text.startswith("```json"):
                    response_text = response_text[7:]
                if response_text.startswith("```"):
                    response_text = response_text[3:]
                if response_text.endswith("```"):
                    response_text = response_text[:-3]

                relation_data = json.loads(response_text)

                related_docs = []
                for rel_doc in relation_data.get("related_documents", []):
                    doc_id = rel_doc.get("id")
                    if 0 <= doc_id < len(doc_info_list):
                        rel_filename = doc_info_list[doc_id]["filename"]

                        for doc in document_list:
                            if doc.get("filename") == rel_filename:
                                doc_copy = doc.copy()
                                doc_copy["relationship_strength"] = rel_doc.get("relationship_strength", "medium")
                                doc_copy["relationship_type"] = rel_doc.get("relationship_type", "related content")
                                doc_copy["relationship_explanation"] = rel_doc.get("relationship_explanation", "")

                                rel_strength = doc_copy["relationship_strength"].lower()
                                doc_copy["similarity_score"] = 7 if rel_strength == "high" else 4 if rel_strength == "medium" else 2

                                related_docs.append(doc_copy)
                                break

                if not related_docs:
                    return {
                        "related_documents": similar_docs,
                        "relationship_type": "keyword_similarity",
                        "relationship_strength": "medium" if similar_docs else "low"
                    }

                combined_docs = []
                for doc in related_docs:
                    if doc.get("relationship_strength") == "high":
                        combined_docs.append(doc)

                for doc in similar_docs:
                    if doc.get("similarity_score", 0) >= 5:
                        if not any(d.get("filename") == doc.get("filename") for d in combined_docs):
                            combined_docs.append(doc)

                for doc in related_docs:
                    if doc.get("relationship_strength") != "high":
                        if not any(d.get("filename") == doc.get("filename") for d in combined_docs):
                            combined_docs.append(doc)

                for doc in similar_docs:
                    if doc.get("similarity_score", 0) < 5:
                        if not any(d.get("filename") == doc.get("filename") for d in combined_docs):
                            combined_docs.append(doc)

                final_docs = combined_docs[:max_results]

                return {
                    "related_documents": final_docs,
                    "relationship_type": "content_relationship",
                    "relationship_strength": "high" if final_docs and (
                        final_docs[0].get("similarity_score", 0) >= 6 or
                        final_docs[0].get("relationship_strength") == "high"
                    ) else "medium"
                }

            except Exception as e:
                logger.error(f"Error in AI relationship analysis: {str(e)}")
                return {
                    "related_documents": similar_docs,
                    "relationship_type": "keyword_match",
                    "relationship_strength": "medium"
                }

        except Exception as e:
            logger.error(f"Error finding related content: {str(e)}")
            return {
                "related_documents": similar_docs,
                "relationship_type": "basic_match",
                "relationship_strength": "low"
            }
