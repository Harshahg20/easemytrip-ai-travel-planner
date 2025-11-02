import React, { useEffect, useRef } from "react";
import { Wrapper } from "@googlemaps/react-wrapper";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";

function MapInner({ center, title }) {
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const markerRef = useRef(null);
  const initializedRef = useRef(false);

  // Initialize map only once when Google Maps is available
  useEffect(() => {
    if (!mapRef.current || initializedRef.current) return;
    
    // Wait for Google Maps to be available
    if (!window.google || !window.google.maps) {
      // Try again after a short delay
      const timeout = setTimeout(() => {
        if (window.google && window.google.maps && mapRef.current && !initializedRef.current) {
          initializeMap();
        }
      }, 100);
      return () => clearTimeout(timeout);
    }

    initializeMap();
    
    function initializeMap() {
      if (!mapRef.current || initializedRef.current) return;
      
      const defaultCenter = center && center.lat && center.lng 
        ? center 
        : { lat: 0, lng: 0 };

      mapInstanceRef.current = new window.google.maps.Map(mapRef.current, {
        center: defaultCenter,
        zoom: 14,
        mapTypeControl: false,
        streetViewControl: false,
      });

      initializedRef.current = true;

      // Create initial marker if center is valid
      if (center && center.lat && center.lng) {
        createOrUpdateMarker(center, title);
      }
    }
  }, []); // Only run once on mount

  // Update map center and marker when center/title changes
  useEffect(() => {
    if (!mapInstanceRef.current || !initializedRef.current) return;
    if (!center || !center.lat || !center.lng || isNaN(center.lat) || isNaN(center.lng)) return;

    console.log("MapInner - Updating map to:", { center, title });

    // Create a new Google Maps LatLng object to ensure fresh coordinates
    const newPosition = new window.google.maps.LatLng(center.lat, center.lng);

    // Update map center with smooth animation
    mapInstanceRef.current.setCenter(newPosition);
    mapInstanceRef.current.setZoom(14);

    // Update or create marker
    createOrUpdateMarker(newPosition, title);
  }, [center?.lat, center?.lng, title]);

  function createOrUpdateMarker(position, markerTitle) {
    if (!mapInstanceRef.current) return;

    if (markerRef.current) {
      // Remove old marker first to ensure no duplicates
      markerRef.current.setMap(null);
    }
    
    // Always create a fresh marker to avoid caching issues
    if (window.google && window.google.maps) {
      markerRef.current = new window.google.maps.Marker({
        position: position,
        map: mapInstanceRef.current,
        title: markerTitle || "Location",
        animation: window.google.maps.Animation.DROP,
      });
      
      console.log("MapInner - Marker created/updated at:", position);
    }
  }

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      if (markerRef.current) {
        markerRef.current.setMap(null);
        markerRef.current = null;
      }
      mapInstanceRef.current = null;
      initializedRef.current = false;
    };
  }, []);

  return <div ref={mapRef} className="w-full h-[60vh]" />;
}

export default function MapModal({ open, onOpenChange, center, title }) {
  // Validate center coordinates
  const validCenter = center && 
    typeof center.lat === "number" && 
    typeof center.lng === "number" &&
    !isNaN(center.lat) && 
    !isNaN(center.lng)
    ? center
    : null;

  // Create a unique key based on center coordinates to force remount when location changes
  // This ensures the map always shows the correct location without caching issues
  const mapKey = validCenter 
    ? `map-${validCenter.lat.toFixed(6)}-${validCenter.lng.toFixed(6)}-${title || 'location'}`
    : `map-${Date.now()}`;

  if (!validCenter) {
    console.warn("Invalid center coordinates:", center);
  }

  // Log for debugging
  useEffect(() => {
    if (validCenter && open) {
      console.log("MapModal - Opening map for:", {
        title,
        center: validCenter,
        mapKey
      });
    }
  }, [validCenter, title, open, mapKey]);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{title || "Location"}</DialogTitle>
        </DialogHeader>
        <div className="rounded-lg overflow-hidden border border-slate-200">
          {validCenter ? (
            <Wrapper 
              apiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY || ""}
              key={mapKey}
            >
              <MapInner center={validCenter} title={title} />
            </Wrapper>
          ) : (
            <div className="w-full h-[60vh] flex items-center justify-center text-slate-500">
              Invalid location coordinates
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
