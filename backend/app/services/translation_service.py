from typing import Dict, List, Any, Optional, Union
import logging
from ..core.config import settings

logger = logging.getLogger(__name__)


class TranslationService:
    """Service for translating content using Google Cloud Translation API"""
    
    def __init__(self):
        self.client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Google Cloud Translation client"""
        try:
            from google.cloud import translate_v2 as translate
            import os
            
            # Try to use API key from settings/env
            api_key = None
            try:
                from dotenv import load_dotenv
                env_paths = [
                    '.env',
                    os.path.join(os.path.dirname(__file__), '..', '..', '.env'),
                    os.path.join(os.getcwd(), '.env'),
                ]
                
                for env_path in env_paths:
                    abs_path = os.path.abspath(env_path)
                    if os.path.exists(abs_path):
                        load_dotenv(dotenv_path=abs_path, override=True)
                        api_key = os.getenv('GOOGLE_AI_API_KEY') or os.getenv('GOOGLE_MAPS_API_KEY')
                        if api_key:
                            api_key = api_key.strip('"').strip("'")
                            break
                
                if not api_key:
                    load_dotenv(override=True)
                    api_key = os.getenv('GOOGLE_AI_API_KEY') or os.getenv('GOOGLE_MAPS_API_KEY')
                    if api_key:
                        api_key = api_key.strip('"').strip("'")
            except Exception as e:
                logger.warning(f"Could not load API key from .env: {e}")
            
            # Fallback to settings
            if not api_key:
                api_key = settings.google_ai_api_key or settings.google_maps_api_key
            
            if api_key:
                # Use API key for authentication
                self.client = translate.Client(api_key=api_key)
                logger.info("✅ Translation service initialized with API key")
            else:
                # Try using default credentials (service account)
                try:
                    self.client = translate.Client()
                    logger.info("✅ Translation service initialized with default credentials")
                except Exception as e:
                    logger.warning(f"Could not initialize translation client: {e}")
                    self.client = None
        except ImportError:
            logger.warning("google-cloud-translate not installed. Translation will be disabled.")
            self.client = None
        except Exception as e:
            logger.error(f"Error initializing translation service: {e}")
            self.client = None
    
    def _get_language_code(self, language: str) -> str:
        """Convert language name to Google Translate language code"""
        language_map = {
            'english': 'en',
            'hindi': 'hi',
            'tamil': 'ta',
            'kannada': 'kn',
            'malayalam': 'ml',
            'telugu': 'te',
        }
        return language_map.get(language.lower(), 'en')
    
    async def translate_text(
        self, 
        text: str, 
        target_language: str,
        source_language: Optional[str] = None
    ) -> str:
        """
        Translate a single text string
        
        Args:
            text: Text to translate
            target_language: Target language (e.g., 'kannada', 'hindi')
            source_language: Source language (optional, auto-detect if not provided)
        
        Returns:
            Translated text
        """
        if not self.client:
            logger.warning("Translation client not available, returning original text")
            return text
        
        if not text or not isinstance(text, str):
            return text
        
        # Skip translation if target is English
        if target_language.lower() == 'english':
            return text
        
        try:
            target_code = self._get_language_code(target_language)
            source_code = self._get_language_code(source_language) if source_language else None
            
            result = self.client.translate(
                text,
                target_language=target_code,
                source_language=source_code
            )
            
            translated_text = result['translatedText']
            logger.debug(f"Translated '{text[:50]}...' to {target_language}")
            return translated_text
        except Exception as e:
            logger.error(f"Error translating text: {e}")
            return text
    
    async def translate_list(
        self,
        texts: List[str],
        target_language: str,
        source_language: Optional[str] = None
    ) -> List[str]:
        """
        Translate a list of texts efficiently (batched)
        
        Args:
            texts: List of texts to translate
            target_language: Target language
            source_language: Source language (optional)
        
        Returns:
            List of translated texts
        """
        if not self.client or not texts:
            return texts or []
        
        # Skip translation if target is English
        if target_language.lower() == 'english':
            return texts
        
        try:
            target_code = self._get_language_code(target_language)
            source_code = self._get_language_code(source_language) if source_language else None
            
            # Filter out empty strings to optimize API calls
            non_empty_texts = [(i, text) for i, text in enumerate(texts) if text and isinstance(text, str) and text.strip()]
            if not non_empty_texts:
                return texts
            
            # Extract just the texts for translation
            texts_to_translate = [text for _, text in non_empty_texts]
            
            # Batch translate all texts at once (more efficient)
            results = self.client.translate(
                texts_to_translate,
                target_language=target_code,
                source_language=source_code
            )
            
            # Reconstruct the full list with translations
            translated_texts = list(texts)  # Start with original
            for idx, (original_idx, _) in enumerate(non_empty_texts):
                if idx < len(results):
                    translated_texts[original_idx] = results[idx]['translatedText']
            
            logger.debug(f"Translated {len(texts_to_translate)} texts to {target_language}")
            return translated_texts
        except Exception as e:
            logger.error(f"Error translating texts: {e}")
            return texts
    
    async def translate_dict(
        self,
        data: Dict[str, Any],
        target_language: str,
        keys_to_translate: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Translate values in a dictionary (optimized with batching)
        
        Args:
            data: Dictionary to translate
            target_language: Target language
            keys_to_translate: List of keys to translate (all string values if None)
        
        Returns:
            Dictionary with translated values
        """
        if not data:
            return data
        
        # Skip translation if target is English
        if target_language.lower() == 'english':
            return data
        
        # Collect all string values to translate in batch (more efficient)
        strings_to_translate = []
        
        def collect_strings(obj):
            """Recursively collect all strings that need translation"""
            if isinstance(obj, dict):
                for key, value in obj.items():
                    # Skip keys that shouldn't be translated
                    if keys_to_translate and key not in keys_to_translate:
                        continue
                    collect_strings(value)
            elif isinstance(obj, list):
                for item in obj:
                    collect_strings(item)
            elif isinstance(obj, str) and obj.strip():
                strings_to_translate.append(obj)
        
        collect_strings(data)
        
        # Batch translate all strings at once (more efficient than one-by-one)
        if strings_to_translate and self.client:
            try:
                target_code = self._get_language_code(target_language)
                results = self.client.translate(
                    strings_to_translate,
                    target_language=target_code
                )
                # Create a mapping of original string to translated text
                translation_map = {
                    original: result['translatedText'] 
                    for original, result in zip(strings_to_translate, results)
                }
                
                # Now apply translations back to the structure
                def apply_translations(obj):
                    if isinstance(obj, dict):
                        return {
                            key: apply_translations(value)
                            if not (keys_to_translate and key not in keys_to_translate)
                            else value
                            for key, value in obj.items()
                        }
                    elif isinstance(obj, list):
                        return [apply_translations(item) for item in obj]
                    elif isinstance(obj, str) and obj.strip():
                        # Look up translation by original string
                        return translation_map.get(obj, obj)
                    else:
                        return obj
                
                translated_result = apply_translations(data)
                logger.debug(f"Batch translated {len(strings_to_translate)} strings to {target_language}")
                return translated_result
            except Exception as e:
                logger.error(f"Error in batch translation: {e}, falling back to sequential")
                # Fallback to sequential translation if batch fails
                pass
        
        # Fallback to original sequential method if batch didn't work
        translated = {}
        for key, value in data.items():
            if keys_to_translate and key not in keys_to_translate:
                translated[key] = value
                continue
            
            if isinstance(value, dict):
                translated[key] = await self.translate_dict(value, target_language, keys_to_translate)
            elif isinstance(value, list):
                translated[key] = await self.translate_list_or_dict_list(value, target_language, keys_to_translate)
            elif isinstance(value, str) and value.strip():
                translated[key] = await self.translate_text(value, target_language)
            else:
                translated[key] = value
        
        return translated
    
    async def translate_list_or_dict_list(
        self,
        items: List[Any],
        target_language: str,
        keys_to_translate: Optional[List[str]] = None
    ) -> List[Any]:
        """Translate a list that may contain dicts or strings (optimized with batching)"""
        if not items:
            return items
        
        # Skip translation if target is English
        if target_language.lower() == 'english':
            return items
        
        # Collect all strings for batch translation
        strings_to_translate = []
        item_types = []  # Track type of each item: 'dict', 'str', or 'other'
        item_indices = []  # Track original indices
        
        for idx, item in enumerate(items):
            if isinstance(item, dict):
                item_types.append('dict')
                item_indices.append(idx)
                # For dicts, we'll handle them separately with translate_dict
            elif isinstance(item, str) and item.strip():
                strings_to_translate.append(item)
                item_types.append('str')
                item_indices.append(idx)
            else:
                item_types.append('other')
                item_indices.append(idx)
        
        # Batch translate all strings at once
        string_translations = {}
        if strings_to_translate and self.client:
            try:
                target_code = self._get_language_code(target_language)
                results = self.client.translate(
                    strings_to_translate,
                    target_language=target_code
                )
                string_translations = {
                    original: result['translatedText']
                    for original, result in zip(strings_to_translate, results)
                }
            except Exception as e:
                logger.error(f"Error in batch string translation: {e}")
        
        # Reconstruct the list with translations
        translated_items = []
        string_idx = 0
        for idx, item in enumerate(items):
            if item_types[idx] == 'dict':
                # Translate dict using the optimized method
                translated_items.append(await self.translate_dict(item, target_language, keys_to_translate))
            elif item_types[idx] == 'str':
                # Use batch translated string
                if item in string_translations:
                    translated_items.append(string_translations[item])
                else:
                    # Fallback to individual translation
                    translated_items.append(await self.translate_text(item, target_language))
                string_idx += 1
            else:
                translated_items.append(item)
        
        return translated_items
    
    async def translate_itinerary(
        self,
        itinerary_data: Dict[str, Any],
        target_language: str
    ) -> Dict[str, Any]:
        """
        Translate itinerary data structure
        
        Args:
            itinerary_data: Itinerary data with activities, meals, accommodation, etc.
            target_language: Target language
        
        Returns:
            Translated itinerary data
        """
        if not itinerary_data:
            return itinerary_data
        
        # Skip translation if target is English
        if target_language.lower() == 'english':
            return itinerary_data
        
        keys_to_translate = [
            'activity', 'description', 'location', 'restaurant', 'meal_type',
            'place', 'name', 'type', 'category', 'title', 'provider', 'route',
            'bookingClass', 'accommodation_type', 'accommodation_name'
        ]
        
        return await self.translate_dict(itinerary_data, target_language, keys_to_translate)


# Create singleton instance
translation_service = TranslationService()

