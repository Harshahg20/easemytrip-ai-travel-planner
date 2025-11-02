"""
Decorator and utilities for automatically caching and translating API responses.
"""

import functools
import logging
from typing import Callable, Any, Optional
from fastapi import Request

logger = logging.getLogger(__name__)


def cache_and_translate_response(
    content_type: str,
    ttl_hours: int = 24,
    require_trip_id: bool = True
):
    """
    Decorator to automatically cache API responses and support translation.
    
    Usage:
        @cache_and_translate_response(content_type="daily_itineraries")
        async def get_itinerary(trip_id: str, language: str = "english", ...):
            # Your endpoint logic
            return response_data
    
    The decorator will:
    1. Cache the response automatically (if trip_id is available)
    2. Translate the response if language is not English
    3. Use cached translations when available
    
    Args:
        content_type: Type of content (e.g., 'daily_itineraries', 'transport_details')
        ttl_hours: Time to live for cache in hours
        require_trip_id: Whether trip_id parameter is required
    """
    def decorator(func: Callable):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            from ..services.enhanced_translation_service import enhanced_translation_service
            
            # Extract trip_id and language from kwargs or args
            trip_id = kwargs.get('trip_id') or (args[0] if args and isinstance(args[0], str) else None)
            language = kwargs.get('language', 'english')
            
            # Get db session if available
            db = kwargs.get('db')
            if db:
                enhanced_translation_service.set_db(db)
            
            # Call the original function
            response_data = await func(*args, **kwargs)
            
            # Cache the response if we have a trip_id
            if trip_id and response_data:
                try:
                    await enhanced_translation_service.ensure_content_cached(
                        trip_id=trip_id,
                        content_type=content_type,
                        content=response_data,
                        ttl_hours=ttl_hours
                    )
                except Exception as e:
                    logger.warning(f"Failed to cache response: {e}")
            
            # Translate if language is not English
            if language and language.lower() != 'english' and response_data:
                try:
                    if trip_id:
                        # Use cached translation if available
                        translated = await enhanced_translation_service.get_translated_content(
                            trip_id=trip_id,
                            content_type=content_type,
                            target_language=language
                        )
                        if translated:
                            return translated
                    
                    # Translate on-the-fly if not cached
                    translated = await enhanced_translation_service.translate_content(
                        content=response_data,
                        target_language=language,
                        content_type=content_type
                    )
                    
                    # Cache the translation if we have trip_id
                    if trip_id and translated:
                        try:
                            await enhanced_translation_service.ensure_content_cached(
                                trip_id=trip_id,
                                content_type=f"{content_type}_translated_{language}",
                                content=translated,
                                ttl_hours=ttl_hours
                            )
                        except Exception as e:
                            logger.warning(f"Failed to cache translation: {e}")
                    
                    return translated
                except Exception as e:
                    logger.error(f"Error translating response: {e}")
                    # Return original if translation fails
                    return response_data
            
            return response_data
        
        return wrapper
    return decorator


def extract_language_from_request(request: Request, default: str = "english") -> str:
    """
    Extract language preference from request.
    Checks query parameter, header, or cookie.
    
    Args:
        request: FastAPI request object
        default: Default language if not found
    
    Returns:
        Language name (e.g., 'english', 'hindi', 'kannada')
    """
    # Check query parameter
    lang = request.query_params.get('language') or request.query_params.get('lang')
    if lang:
        return lang.lower()
    
    # Check header
    lang = request.headers.get('X-Language') or request.headers.get('Accept-Language')
    if lang:
        # Extract language from Accept-Language header if needed
        if ',' in lang:
            lang = lang.split(',')[0].strip()
        # Remove quality values (e.g., "en;q=0.9" -> "en")
        if ';' in lang:
            lang = lang.split(';')[0].strip()
        return lang.lower()
    
    # Check cookie
    lang = request.cookies.get('language') or request.cookies.get('lang')
    if lang:
        return lang.lower()
    
    return default

