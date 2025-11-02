import React, { useRef } from "react";
import { ChevronLeft, ChevronRight, Image as ImageIcon } from "lucide-react";

export default function DestinationCarousel({ 
  tripId, 
  destination, 
  photos = [], 
  loading = false,
  error = null 
}) {
  const containerRef = useRef(null);

  const scrollBy = (dx) => {
    if (containerRef.current) {
      containerRef.current.scrollBy({ left: dx, behavior: "smooth" });
    }
  };

  if (loading) {
    return (
      <div className="w-full h-64 md:h-80 lg:h-96 rounded-xl overflow-hidden border border-slate-200 mb-6 flex items-center justify-center text-slate-400 bg-slate-50">
        <ImageIcon className="w-6 h-6 mr-2 animate-pulse" /> Loading photos...
      </div>
    );
  }

  if (error || !photos.length) {
    return (
      <div className="w-full h-64 md:h-80 lg:h-96 rounded-xl overflow-hidden border border-slate-200 mb-6 flex items-center justify-center text-slate-400 bg-slate-50">
        <ImageIcon className="w-6 h-6 mr-2" /> 
        {error || `No photos found for ${destination}`}
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
