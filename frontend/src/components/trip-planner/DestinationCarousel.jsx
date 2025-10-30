import React, { useEffect, useState, useRef } from "react";
import { ChevronLeft, ChevronRight, Image as ImageIcon } from "lucide-react";
import { tripService } from "../../services/api";

export default function DestinationCarousel({ tripId, destination }) {
  const [photos, setPhotos] = useState([]);
  const [loading, setLoading] = useState(true);
  const containerRef = useRef(null);

  useEffect(() => {
    let mounted = true;
    async function load() {
      try {
        const data = await tripService.getDestinationPhotos(tripId);
        if (mounted) setPhotos(data.photos || []);
      } catch (e) {
        console.error("Failed to load destination photos", e);
      } finally {
        if (mounted) setLoading(false);
      }
    }
    if (tripId) load();
    return () => (mounted = false);
  }, [tripId]);

  const scrollBy = (dx) => {
    if (containerRef.current) {
      containerRef.current.scrollBy({ left: dx, behavior: "smooth" });
    }
  };

  if (loading) {
    return (
      <div className="w-full h-64 md:h-80 lg:h-96 rounded-xl overflow-hidden border border-slate-200 mb-6 flex items-center justify-center text-slate-400">
        <ImageIcon className="w-6 h-6 mr-2" /> Loading photos...
      </div>
    );
  }

  if (!photos.length) {
    return (
      <div className="w-full h-64 md:h-80 lg:h-96 rounded-xl overflow-hidden border border-slate-200 mb-6 flex items-center justify-center text-slate-400">
        <ImageIcon className="w-6 h-6 mr-2" /> No photos found for {destination}
      </div>
    );
  }

  return (
    <div className="relative mb-6">
      <div
        ref={containerRef}
        className="w-full h-64 md:h-80 lg:h-96 rounded-xl overflow-x-auto whitespace-nowrap scroll-smooth snap-x snap-mandatory border border-slate-200"
      >
        {photos.map((url, idx) => (
          <img
            key={idx}
            src={url}
            alt={`${destination} ${idx + 1}`}
            className="inline-block w-full h-full object-cover snap-start"
            loading="lazy"
          />
        ))}
      </div>
      <button
        type="button"
        onClick={() => scrollBy(-400)}
        className="hidden md:flex absolute left-3 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white border border-slate-200 rounded-full w-9 h-9 items-center justify-center shadow"
      >
        <ChevronLeft className="w-5 h-5" />
      </button>
      <button
        type="button"
        onClick={() => scrollBy(400)}
        className="hidden md:flex absolute right-3 top-1/2 -translate-y-1/2 bg-white/80 hover:bg-white border border-slate-200 rounded-full w-9 h-9 items-center justify-center shadow"
      >
        <ChevronRight className="w-5 h-5" />
      </button>
    </div>
  );
}
