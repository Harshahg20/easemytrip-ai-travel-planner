import { useState, useEffect, useCallback } from "react";
import { useLanguage } from "../components/language/LanguageProvider";
import { tripService } from "../services/api";

/**
 * Hook to translate dynamic content using Google Translate API
 */
export const useTranslation = () => {
  const { currentLanguage } = useLanguage();
  const [isTranslating, setIsTranslating] = useState(false);
  const [translationCache, setTranslationCache] = useState({});

  // Generate cache key from content and language
  const getCacheKey = useCallback((content, language) => {
    if (typeof content === "string") {
      return `${language}:${content}`;
    }
    return `${language}:${JSON.stringify(content)}`;
  }, []);

  // Translate content (cached)
  const translate = useCallback(
    async (content, options = {}) => {
      // Skip translation if language is English
      if (currentLanguage === "english") {
        return content;
      }

      // Skip if content is empty or invalid
      if (
        !content ||
        (typeof content !== "string" && typeof content !== "object")
      ) {
        return content;
      }

      // Check cache
      const cacheKey = getCacheKey(content, currentLanguage);
      if (translationCache[cacheKey]) {
        return translationCache[cacheKey];
      }

      // If no translate option is provided, return original
      if (options.skipTranslation) {
        return content;
      }

      setIsTranslating(true);
      try {
        let translated;

        if (typeof content === "string") {
          // Translate single text
          const result = await tripService.translateTexts(
            [content],
            currentLanguage
          );
          translated = result[0];
        } else if (Array.isArray(content)) {
          // Translate array
          translated = await tripService.translateContent(
            content,
            currentLanguage
          );
        } else if (typeof content === "object") {
          // Translate object/dict
          if (content.activities || content.meals || content.accommodation) {
            // Itinerary structure
            translated = await tripService.translateItinerary(
              content,
              currentLanguage
            );
          } else {
            // Generic object
            translated = await tripService.translateContent(
              content,
              currentLanguage
            );
          }
        } else {
          translated = content;
        }

        // Cache the result
        setTranslationCache((prev) => ({
          ...prev,
          [cacheKey]: translated,
        }));

        return translated;
      } catch (error) {
        console.error("Translation error:", error);
        // Return original content on error
        return content;
      } finally {
        setIsTranslating(false);
      }
    },
    [currentLanguage, translationCache, getCacheKey]
  );

  // Clear cache when language changes
  useEffect(() => {
    setTranslationCache({});
  }, [currentLanguage]);

  return {
    translate,
    isTranslating,
    currentLanguage,
  };
};

/**
 * Hook to translate itinerary data specifically
 */
export const useItineraryTranslation = () => {
  const { translate, isTranslating, currentLanguage } = useTranslation();

  const translateItinerary = useCallback(
    async (itineraryData) => {
      if (!itineraryData || currentLanguage === "english") {
        return itineraryData;
      }

      return await translate(itineraryData, {
        skipTranslation: false,
      });
    },
    [translate, currentLanguage]
  );

  return {
    translateItinerary,
    isTranslating,
    currentLanguage,
  };
};

/**
 * Hook for batch translation of cached content by type
 * Uses cached content from backend and translates in batches
 */
export const useBatchTranslation = () => {
  const { currentLanguage } = useLanguage();
  const [isTranslating, setIsTranslating] = useState(false);
  const [translatedContent, setTranslatedContent] = useState({});

  /**
   * Translate cached content in batches by content type
   * @param {string} tripId - Trip ID
   * @param {string[]} contentTypes - Array of content types to translate
   * @returns {Promise<Object>} Translated content organized by content type
   */
  const translateCachedContent = useCallback(
    async (tripId, contentTypes) => {
      if (!tripId || !contentTypes || contentTypes.length === 0) {
        return {};
      }

      if (currentLanguage === "english") {
        return {};
      }

      setIsTranslating(true);
      try {
        const translated = await tripService.translateCachedContent(
          tripId,
          contentTypes,
          currentLanguage
        );

        setTranslatedContent((prev) => ({
          ...prev,
          ...translated,
        }));

        return translated;
      } catch (error) {
        console.error("Batch translation error:", error);
        return {};
      } finally {
        setIsTranslating(false);
      }
    },
    [currentLanguage]
  );

  /**
   * Translate all daily itineraries for a trip
   * @param {string} tripId - Trip ID
   * @returns {Promise<Object>} Translated itineraries organized by day number
   */
  const translateAllDailyItineraries = useCallback(
    async (tripId) => {
      if (!tripId) {
        return {};
      }

      if (currentLanguage === "english") {
        return {};
      }

      setIsTranslating(true);
      try {
        const translated = await tripService.translateDailyItineraries(
          tripId,
          currentLanguage
        );

        setTranslatedContent((prev) => ({
          ...prev,
          daily_itineraries: translated,
        }));

        return translated;
      } catch (error) {
        console.error("Daily itineraries translation error:", error);
        return {};
      } finally {
        setIsTranslating(false);
      }
    },
    [currentLanguage]
  );

  // Clear translated content when language changes
  useEffect(() => {
    setTranslatedContent({});
  }, [currentLanguage]);

  return {
    translateCachedContent,
    translateAllDailyItineraries,
    translatedContent,
    isTranslating,
    currentLanguage,
  };
};
