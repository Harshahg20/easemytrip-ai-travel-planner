"""
Content Cache Service for storing API responses and enabling efficient translation.

Uses in-memory cache as primary storage with optional Redis backend for production.
Organizes content by trip_id and content_type for efficient batch translation.
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from collections import defaultdict
import hashlib

logger = logging.getLogger(__name__)


class ContentCacheService:
    """
    Content cache service that stores API responses for efficient translation.
    
    Features:
    - In-memory cache with TTL (primary)
    - Optional Redis backend for production/scaling
    - Organized by trip_id and content_type
    - Automatic expiration of stale content
    """
    
    def __init__(self, default_ttl_hours: int = 24, enable_redis: bool = False):
        """
        Initialize the content cache service.
        
        Args:
            default_ttl_hours: Default time-to-live in hours for cached content
            enable_redis: Whether to use Redis as backend (if available)
        """
        self.default_ttl_hours = default_ttl_hours
        self.enable_redis = enable_redis
        
        # In-memory cache structure:
        # {trip_id: {content_type: {cache_key: {data, expires_at, created_at}}}}
        self._cache: Dict[str, Dict[str, Dict[str, Dict[str, Any]]]] = defaultdict(
            lambda: defaultdict(dict)
        )
        
        # Lock for thread-safe operations
        self._lock = asyncio.Lock()
        
        # Redis client (optional)
        self.redis_client = None
        if enable_redis:
            self._initialize_redis()
        
        # Background task for cleanup
        self._cleanup_task = None
        self._start_cleanup_task()
        
        logger.info(f"✅ Content cache service initialized (Redis: {enable_redis})")
    
    def _initialize_redis(self):
        """Initialize Redis client if available"""
        try:
            import redis.asyncio as redis
            import os
            
            # Try to get Redis URL from environment or use default
            redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
            
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True
                )
                logger.info(f"✅ Redis client initialized: {redis_url}")
                # Note: Connection test will happen on first use
            except Exception as e:
                logger.warning(f"Could not connect to Redis: {e}. Using in-memory cache only.")
                self.redis_client = None
                self.enable_redis = False
        except ImportError:
            logger.warning("redis package not installed. Using in-memory cache only.")
            self.redis_client = None
            self.enable_redis = False
    
    def _start_cleanup_task(self):
        """Start background task to clean up expired cache entries"""
        # Cleanup will happen on access, no need for background task in simple implementation
        # For production with Redis, you might want to use a separate cleanup service
        pass
    
    def _generate_cache_key(self, content: Any) -> str:
        """Generate a cache key from content"""
        content_str = json.dumps(content, sort_keys=True, default=str)
        return hashlib.md5(content_str.encode()).hexdigest()
    
    async def _cleanup_expired_entries(self):
        """Remove expired cache entries"""
        async with self._lock:
            now = datetime.utcnow()
            expired_count = 0
            
            for trip_id in list(self._cache.keys()):
                for content_type in list(self._cache[trip_id].keys()):
                    expired_keys = [
                        key for key, value in self._cache[trip_id][content_type].items()
                        if value.get('expires_at') and value['expires_at'] < now
                    ]
                    for key in expired_keys:
                        del self._cache[trip_id][content_type][key]
                        expired_count += 1
                    
                    # Remove empty content_type dicts
                    if not self._cache[trip_id][content_type]:
                        del self._cache[trip_id][content_type]
                
                # Remove empty trip_id dicts
                if not self._cache[trip_id]:
                    del self._cache[trip_id]
            
            if expired_count > 0:
                logger.debug(f"Cleaned up {expired_count} expired cache entries")
    
    async def store(
        self,
        trip_id: str,
        content_type: str,
        content: Any,
        ttl_hours: Optional[int] = None
    ) -> str:
        """
        Store content in cache.
        
        Args:
            trip_id: Trip identifier
            content_type: Type of content (e.g., 'daily_itineraries', 'trip_options', 'transport_details')
            content: Content to store (must be JSON-serializable)
            ttl_hours: Time-to-live in hours (uses default if None)
        
        Returns:
            Cache key for the stored content
        """
        async with self._lock:
            ttl_hours = ttl_hours or self.default_ttl_hours
            cache_key = self._generate_cache_key(content)
            now = datetime.utcnow()
            expires_at = now + timedelta(hours=ttl_hours)
            
            cache_entry = {
                'data': content,
                'created_at': now.isoformat(),
                'expires_at': expires_at.isoformat(),
            }
            
            # Store in memory
            self._cache[trip_id][content_type][cache_key] = cache_entry
            
            # Store in Redis if enabled
            if self.redis_client:
                try:
                    redis_key = f"cache:{trip_id}:{content_type}:{cache_key}"
                    await self.redis_client.setex(
                        redis_key,
                        ttl_hours * 3600,  # Convert to seconds
                        json.dumps(cache_entry, default=str)
                    )
                except Exception as e:
                    logger.warning(f"Failed to store in Redis: {e}")
            
            logger.debug(f"Cached {content_type} for trip {trip_id} (key: {cache_key[:8]}...)")
            return cache_key
    
    async def get(
        self,
        trip_id: str,
        content_type: str,
        cache_key: Optional[str] = None
    ) -> Optional[Any]:
        """
        Retrieve content from cache.
        
        Args:
            trip_id: Trip identifier
            content_type: Type of content
            cache_key: Optional specific cache key (returns latest if None)
        
        Returns:
            Cached content or None if not found/expired
        """
        async with self._lock:
            # Try memory first
            if trip_id in self._cache and content_type in self._cache[trip_id]:
                if cache_key:
                    entry = self._cache[trip_id][content_type].get(cache_key)
                    if entry:
                        # Check expiration
                        expires_at = datetime.fromisoformat(entry['expires_at'])
                        if datetime.utcnow() < expires_at:
                            return entry['data']
                        else:
                            # Expired, remove it
                            del self._cache[trip_id][content_type][cache_key]
                else:
                    # Get latest entry
                    entries = self._cache[trip_id][content_type]
                    if entries:
                        # Get most recently created entry that's not expired
                        valid_entries = {
                            k: v for k, v in entries.items()
                            if datetime.fromisoformat(v['expires_at']) > datetime.utcnow()
                        }
                        if valid_entries:
                            latest_key = max(
                                valid_entries.keys(),
                                key=lambda k: valid_entries[k]['created_at']
                            )
                            return valid_entries[latest_key]['data']
            
            # Try Redis if enabled
            if self.redis_client:
                try:
                    if cache_key:
                        redis_key = f"cache:{trip_id}:{content_type}:{cache_key}"
                    else:
                        # Get all keys for this trip_id and content_type
                        pattern = f"cache:{trip_id}:{content_type}:*"
                        keys = await self.redis_client.keys(pattern)
                        if keys:
                            # Get the most recent one
                            redis_key = keys[-1]
                        else:
                            return None
                    
                    cached_data = await self.redis_client.get(redis_key)
                    if cached_data:
                        entry = json.loads(cached_data)
                        # Also populate memory cache
                        self._cache[trip_id][content_type][cache_key or redis_key.split(':')[-1]] = entry
                        return entry['data']
                except Exception as e:
                    logger.warning(f"Failed to retrieve from Redis: {e}")
            
            return None
    
    async def get_all_by_type(
        self,
        trip_id: str,
        content_type: str
    ) -> List[Dict[str, Any]]:
        """
        Get all cached content of a specific type for a trip.
        Useful for batch translation.
        
        Args:
            trip_id: Trip identifier
            content_type: Type of content
        
        Returns:
            List of cached content items with their keys
        """
        async with self._lock:
            results = []
            now = datetime.utcnow()
            
            # Get from memory
            if trip_id in self._cache and content_type in self._cache[trip_id]:
                for cache_key, entry in self._cache[trip_id][content_type].items():
                    expires_at = datetime.fromisoformat(entry['expires_at'])
                    if now < expires_at:
                        results.append({
                            'cache_key': cache_key,
                            'data': entry['data'],
                            'created_at': entry['created_at']
                        })
            
            # Also check Redis if enabled
            if self.redis_client and not results:
                try:
                    pattern = f"cache:{trip_id}:{content_type}:*"
                    keys = await self.redis_client.keys(pattern)
                    for key in keys:
                        cached_data = await self.redis_client.get(key)
                        if cached_data:
                            entry = json.loads(cached_data)
                            expires_at = datetime.fromisoformat(entry['expires_at'])
                            if now < expires_at:
                                cache_key = key.split(':')[-1]
                                results.append({
                                    'cache_key': cache_key,
                                    'data': entry['data'],
                                    'created_at': entry['created_at']
                                })
                except Exception as e:
                    logger.warning(f"Failed to retrieve from Redis: {e}")
            
            return results
    
    async def clear_trip(self, trip_id: str):
        """Clear all cached content for a trip"""
        async with self._lock:
            if trip_id in self._cache:
                del self._cache[trip_id]
            
            if self.redis_client:
                try:
                    pattern = f"cache:{trip_id}:*"
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Failed to clear Redis cache: {e}")
            
            logger.debug(f"Cleared cache for trip {trip_id}")
    
    async def clear_type(self, trip_id: str, content_type: str):
        """Clear cached content of a specific type for a trip"""
        async with self._lock:
            if trip_id in self._cache and content_type in self._cache[trip_id]:
                del self._cache[trip_id][content_type]
            
            if self.redis_client:
                try:
                    pattern = f"cache:{trip_id}:{content_type}:*"
                    keys = await self.redis_client.keys(pattern)
                    if keys:
                        await self.redis_client.delete(*keys)
                except Exception as e:
                    logger.warning(f"Failed to clear Redis cache: {e}")
    
    async def get_cache_stats(self, trip_id: Optional[str] = None) -> Dict[str, Any]:
        """Get cache statistics"""
        async with self._lock:
            stats = {
                'total_trips': len(self._cache),
                'trips': {}
            }
            
            for tid, content_types in self._cache.items():
                if trip_id and tid != trip_id:
                    continue
                
                trip_stats = {
                    'content_types': {},
                    'total_entries': 0
                }
                
                for ctype, entries in content_types.items():
                    valid_entries = {
                        k: v for k, v in entries.items()
                        if datetime.fromisoformat(v['expires_at']) > datetime.utcnow()
                    }
                    trip_stats['content_types'][ctype] = len(valid_entries)
                    trip_stats['total_entries'] += len(valid_entries)
                
                stats['trips'][tid] = trip_stats
            
            return stats


# Create singleton instance
# Enable Redis if REDIS_URL environment variable is set
import os
enable_redis = bool(os.getenv('REDIS_URL'))
content_cache_service = ContentCacheService(
    default_ttl_hours=24,
    enable_redis=enable_redis
)

