import React, { useEffect, useRef } from "react";
import { MapContainer, TileLayer, Marker, Popup } from "react-leaflet";
import "leaflet/dist/leaflet.css";
import L from "leaflet";
import { useLanguage } from "../language/LanguageProvider";

// Fix for default icon issue with webpack
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl:
    "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png",
  iconUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png",
  shadowUrl: "https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png",
});

export default function InteractiveMap({ dayData }) {
  const { t } = useLanguage();
  const mapRef = useRef(null);

  const getMarkers = () => {
    if (!dayData) return [];

    const markers = [];
    if (dayData.activities) {
      dayData.activities.forEach((item) => {
        if (item.coordinates) markers.push({ ...item, type: t("activities") });
      });
    }
    if (dayData.meals) {
      dayData.meals.forEach((item) => {
        if (item.coordinates)
          markers.push({
            ...item,
            name: item.restaurant,
            type: t("meals"),
            location: item.location,
          });
      });
    }
    if (dayData.accommodation && dayData.accommodation.coordinates) {
      markers.push({ ...dayData.accommodation, type: t("accommodation") });
    }

    return markers.filter(
      (marker) =>
        marker.coordinates && marker.coordinates.lat && marker.coordinates.lng
    );
  };

  const markers = getMarkers();

  useEffect(() => {
    if (mapRef.current && markers.length > 0) {
      const bounds = L.latLngBounds(
        markers.map((m) => [m.coordinates.lat, m.coordinates.lng])
      );
      mapRef.current.fitBounds(bounds, { padding: [50, 50] });
    }
  }, [dayData, markers]);

  if (!dayData || markers.length === 0) {
    return (
      <div className="aspect-video bg-slate-100 rounded-lg flex items-center justify-center">
        <div className="text-center text-slate-500">
          <p>{t("selectDayPrompt")}</p>
        </div>
      </div>
    );
  }

  const center =
    markers.length > 0
      ? [markers[0].coordinates.lat, markers[0].coordinates.lng]
      : [28.6139, 77.209];

  return (
    <div className="aspect-video h-[500px] w-full rounded-lg overflow-hidden">
      <MapContainer
        center={center}
        zoom={12}
        scrollWheelZoom={false}
        className="h-full w-full"
        ref={mapRef}
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        {markers.map((marker, index) => (
          <Marker
            key={index}
            position={[marker.coordinates.lat, marker.coordinates.lng]}
          >
            <Popup>
              <div className="font-bold">{marker.name || marker.activity}</div>
              <div className="text-sm text-slate-600">{marker.location}</div>
              <div className="text-xs text-blue-600 font-semibold">
                {marker.type}
              </div>
            </Popup>
          </Marker>
        ))}
      </MapContainer>
    </div>
  );
}
