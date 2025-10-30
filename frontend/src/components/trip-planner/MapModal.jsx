import React from "react";
import { Wrapper } from "@googlemaps/react-wrapper";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";

function MapInner({ center, title }) {
  const ref = React.useRef(null);
  React.useEffect(() => {
    if (!ref.current) return;
    const map = new window.google.maps.Map(ref.current, {
      center,
      zoom: 14,
      mapTypeControl: false,
      streetViewControl: false,
    });
    new window.google.maps.Marker({ position: center, map, title });
  }, [center, title]);
  return <div ref={ref} className="w-full h-[60vh]" />;
}

export default function MapModal({ open, onOpenChange, center, title }) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl">
        <DialogHeader>
          <DialogTitle>{title || "Location"}</DialogTitle>
        </DialogHeader>
        <div className="rounded-lg overflow-hidden border border-slate-200">
          <Wrapper apiKey={process.env.REACT_APP_GOOGLE_MAPS_API_KEY || ""}>
            <MapInner center={center} title={title} />
          </Wrapper>
        </div>
      </DialogContent>
    </Dialog>
  );
}
