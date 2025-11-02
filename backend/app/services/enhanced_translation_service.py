"""
Enhanced Translation Service that combines:
1. In-memory content caching (session-level)
2. Database translation caching (persistent)
3. Automatic caching of API responses
4. On-demand translation when language changes

This service ensures all API responses are cached and can be translated efficiently.
"""

import logging
from typing import Dict, List, Any, Optional
from sqlalchemy.orm import Session
from .translation_service import translation_service, translation_cache_service
from .content_cache_service import content_cache_service

logger = logging.getLogger(__name__)


class EnhancedTranslationService:
    """
    Enhanced translation service that manages both content caching and translation caching.
    This is the main service that should be used for all translation needs.
    """
    
    def __init__(self):
        self.content_cache = content_cache_service
        self.translation_service = translation_service
        self.db_translation_cache = translation_cache_service
    
    def set_db(self, db_session: Session):
        """Set database session for translation caching"""
        self.db_translation_cache.set_db(db_session)
    
    def _get_language_code(self, language: str) -> str:
        """Convert language name to language code"""
        language_map = {
            'english': 'en',
            'hindi': 'hi',
            'tamil': 'ta',
            'kannada': 'kn',
            'malayalam': 'ml',
            'telugu': 'te',
        }
        return language_map.get(language.lower(), 'en')
    
    async def cache_api_response(
        self,
        trip_id: str,
        content_type: str,
        content: Any,
        ttl_hours: int = 24
    ) -> str:
        """
        Cache API response in content cache (session-level).
        This stores the original English content.
        
        Args:
            trip_id: Trip identifier
            content_type: Type of content (e.g., 'daily_itineraries', 'transport_details')
            content: Content to cache
            ttl_hours: Time to live in hours
        
        Returns:
            Cache key
        """
        cache_key = await self.content_cache.store(
            trip_id=trip_id,
            content_type=content_type,
            content=content,
            ttl_hours=ttl_hours
        )
        logger.debug(f"Cached {content_type} for trip {trip_id}")
        return cache_key
    
    async def get_translated_content(
        self,
        trip_id: str,
        content_type: str,
        target_language: str,
        cache_key: Optional[str] = None
    ) -> Optional[Any]:
        """
        Get translated content using multi-level caching:
        1. Check database translation cache
        2. Check content cache and translate if needed
        3. Return translated content
        
        Args:
            trip_id: Trip identifier
            content_type: Type of content
            target_language: Target language (e.g., 'hindi', 'kannada')
            cache_key: Optional specific cache key
        
        Returns:
            Translated content or None if not found
        """
        # Skip if English
        if target_language.lower() == 'english':
            return await self.content_cache.get(trip_id, content_type, cache_key)
        
        target_lang_code = self._get_language_code(target_language)
        
        # Step 1: Get original content from content cache
        original_content = await self.content_cache.get(trip_id, content_type, cache_key)
        if not original_content:
            return None
        
        # Step 2: Generate content hash
        content_hash = self.translation_service._generate_content_hash(original_content)
        
        # Step 3: Check database translation cache
        cached_translation = await self.db_translation_cache.get_translation(
            content_hash=content_hash,
            content_type=content_type,
            target_language=target_lang_code,
            source_language='en'
        )
        
        if cached_translation:
            logger.debug(f"Retrieved translation from DB cache for {content_type} ({target_language})")
            return cached_translation
        
        # Step 4: Translate content (not cached)
        logger.info(f"Translating {content_type} to {target_language} (not in cache)")
        translated_content = await self.translate_content(
            original_content,
            target_language,
            content_type
        )
        
        # Step 5: Store translation in database cache
        if self.db_translation_cache._db:
            await self.db_translation_cache.store_translation(
                content_hash=content_hash,
                content_type=content_type,
                original_content=original_content,
                translated_content=translated_content,
                target_language=target_lang_code,
                source_language='en',
                trip_id=trip_id,
                cache_key=cache_key,
                ttl_hours=168  # 7 days
            )
        
        return translated_content
    
    async def translate_content(
        self,
        content: Any,
        target_language: str,
        content_type: Optional[str] = None
    ) -> Any:
        """
        Translate content using the translation service.
        
        Args:
            content: Content to translate
            target_language: Target language
            content_type: Optional content type for specialized translation
        
        Returns:
            Translated content
        """
        if not content:
            return content
        
        if target_language.lower() == 'english':
            return content
        
        # Use specialized translation for itinerary content
        if content_type in ['daily_itineraries', 'itinerary', 'trip_options']:
            if isinstance(content, list):
                translated = []
                for item in content:
                    if isinstance(item, dict):
                        translated.append(
                            await self.translation_service.translate_itinerary(
                                item, target_language
                            )
                        )
                    else:
                        translated.append(item)
                return translated
            elif isinstance(content, dict):
                return await self.translation_service.translate_itinerary(
                    content, target_language
                )
        
        # Use generic translation for other content types
        if isinstance(content, dict):
            # Determine keys to translate based on content type
            keys_to_translate = None
            if content_type == 'transport_details':
                keys_to_translate = [
                    'route', 'description', 'provider', 'transportation_type',
                    'mode', 'instructions', 'tips', 'details'
                ]
            elif content_type in ['smart_adjustments', 'adjustments']:
                keys_to_translate = [
                    'title', 'description', 'action', 'suggestions', 'severity',
                    'attraction', 'place', 'name'
                ]
            elif content_type in ['recommendations', 'attractions']:
                keys_to_translate = [
                    'name', 'description', 'category', 'location', 'type',
                    'cuisine', 'specialties', 'amenities', 'tips'
                ]
            
            return await self.translation_service.translate_dict(
                content, target_language, keys_to_translate
            )
        elif isinstance(content, list):
            return await self.translation_service.translate_list_or_dict_list(
                content, target_language
            )
        else:
            return await self.translation_service.translate_text(
                content, target_language
            )
    
    async def translate_cached_content_batch(
        self,
        trip_id: str,
        content_types: List[str],
        target_language: str
    ) -> Dict[str, Any]:
        """
        Translate multiple cached content types in batch.
        
        Args:
            trip_id: Trip identifier
            content_types: List of content types to translate
            target_language: Target language
        
        Returns:
            Dictionary mapping content_type to translated content
        """
        results = {}
        
        for content_type in content_types:
            try:
                translated = await self.get_translated_content(
                    trip_id=trip_id,
                    content_type=content_type,
                    target_language=target_language
                )
                
                if translated:
                    results[content_type] = translated
            except Exception as e:
                logger.error(f"Error translating {content_type}: {e}")
                # Continue with other content types
        
        return results
    
    async def ensure_content_cached(
        self,
        trip_id: str,
        content_type: str,
        content: Any,
        ttl_hours: int = 24
    ):
        """
        Ensure content is cached. If already cached, do nothing.
        Useful for automatically caching API responses.
        
        Args:
            trip_id: Trip identifier
            content_type: Type of content
            content: Content to cache
            ttl_hours: Time to live in hours
        """
        # Check if already cached
        existing = await self.content_cache.get(trip_id, content_type)
        if existing:
            return  # Already cached
        
        # Cache it
        await self.cache_api_response(
            trip_id=trip_id,
            content_type=content_type,
            content=content,
            ttl_hours=ttl_hours
        )


# Create singleton instance
enhanced_translation_service = EnhancedTranslationService()

