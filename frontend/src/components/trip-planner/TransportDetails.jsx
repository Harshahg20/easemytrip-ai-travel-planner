import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import {
  Plane,
  Train,
  Bus,
  Car,
  MapPin,
  Clock,
  DollarSign,
  Calendar,
  ArrowRight,
  Luggage,
} from "lucide-react";
import { useLanguage } from "../language/LanguageProvider";

export default function TransportDetails({ trip, dailyItineraries }) {
  const { t } = useLanguage();

  // Generate transport recommendations based on user preference
  const getTransportRecommendations = () => {
    const preference = trip.transportation_preference || "mixed";
    const duration = dailyItineraries.length;
    const travelers = trip.travelers;

    const recommendations = [];

    // Flight recommendations
    if (preference === "private" || preference === "mixed") {
      recommendations.push({
        type: "flight",
        title: "Flight to Destination",
        provider: "IndiGo / Air India",
        route: `Delhi → ${trip.destination}`,
        duration: "2h 30m",
        cost: Math.round((trip.total_budget * 0.25) / travelers),
        departure: "08:30 AM",
        arrival: "11:00 AM",
        bookingClass: travelers > 2 ? "Economy" : "Business",
        icon: Plane,
        color: "bg-blue-500",
        lightColor: "bg-blue-50",
        borderColor: "border-blue-200",
      });

      recommendations.push({
        type: "flight",
        title: "Return Flight",
        provider: "SpiceJet / Vistara",
        route: `${trip.destination} → Delhi`,
        duration: "2h 45m",
        cost: Math.round((trip.total_budget * 0.25) / travelers),
        departure: "06:15 PM",
        arrival: "09:00 PM",
        bookingClass: travelers > 2 ? "Economy" : "Business",
        icon: Plane,
        color: "bg-blue-500",
        lightColor: "bg-blue-50",
        borderColor: "border-blue-200",
      });
    }

    // Train recommendations
    if (preference === "public" || preference === "mixed") {
      recommendations.push({
        type: "train",
        title: "Express Train to Destination",
        provider: "Indian Railways",
        route: `New Delhi → ${trip.destination}`,
        duration: "8h 45m",
        cost: Math.round((trip.total_budget * 0.15) / travelers),
        departure: "10:30 PM",
        arrival: "07:15 AM (+1)",
        bookingClass: travelers > 3 ? "3A" : "2A",
        icon: Train,
        color: "bg-green-500",
        lightColor: "bg-green-50",
        borderColor: "border-green-200",
      });
    }

    // Local transport
    if (duration > 1) {
      const localTransport =
        preference === "private"
          ? {
              type: "car",
              title: "Private Car Rental",
              provider: "Zoomcar / Ola Outstation",
              route: "Local city transport",
              duration: `${duration} days`,
              cost: Math.round(trip.total_budget * 0.2),
              departure: "Available 24/7",
              arrival: "Drop at hotel",
              bookingClass: travelers > 4 ? "SUV" : "Sedan",
              icon: Car,
              color: "bg-purple-500",
              lightColor: "bg-purple-50",
              borderColor: "border-purple-200",
            }
          : {
              type: "bus",
              title: "Local Bus Pass",
              provider: "City Transport Corporation",
              route: "All major attractions",
              duration: `${duration} days`,
              cost: Math.round(trip.total_budget * 0.05),
              departure: "06:00 AM - 11:00 PM",
              arrival: "Multiple stops",
              bookingClass: "AC Bus",
              icon: Bus,
              color: "bg-orange-500",
              lightColor: "bg-orange-50",
              borderColor: "border-orange-200",
            };

      recommendations.push(localTransport);
    }

    return recommendations;
  };

  const transportOptions = getTransportRecommendations();

  const getPreferenceText = (preference) => {
    switch (preference) {
      case "public":
        return "Public Transport Focused";
      case "private":
        return "Private Transport Focused";
      case "mixed":
        return "Mixed Transport Options";
      default:
        return "Transport Options";
    }
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-6">
        <h3 className="text-lg font-semibold text-slate-800 mb-2">
          Travel & Transport
        </h3>
        <Badge variant="outline" className="bg-slate-50 text-slate-700">
          {getPreferenceText(trip.transportation_preference)}
        </Badge>
      </div>

      {transportOptions.map((transport, index) => (
        <Card
          key={index}
          className={`border ${transport.borderColor} ${transport.lightColor}`}
        >
          <CardHeader>
            <CardTitle className="flex items-center gap-3">
              <div
                className={`w-10 h-10 ${transport.color} rounded-full flex items-center justify-center`}
              >
                <transport.icon className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="text-lg font-semibold text-slate-800">
                  {transport.title}
                </div>
                <div className="text-sm text-slate-500">
                  {transport.provider}
                </div>
              </div>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <MapPin className="w-4 h-4" />
                  <span>{transport.route}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Clock className="w-4 h-4" />
                  <span>{transport.duration}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <DollarSign className="w-4 h-4" />
                  <span>₹{transport.cost.toLocaleString()} per person</span>
                </div>
              </div>

              <div className="space-y-3">
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Calendar className="w-4 h-4" />
                  <span>Departure: {transport.departure}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <ArrowRight className="w-4 h-4" />
                  <span>Arrival: {transport.arrival}</span>
                </div>
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Luggage className="w-4 h-4" />
                  <span>Class: {transport.bookingClass}</span>
                </div>
              </div>
            </div>

            <div className="pt-4 border-t border-slate-200">
              <div className="text-center">
                <div className="text-sm text-slate-500">
                  Total for {trip.travelers} travelers: ₹
                  {(transport.cost * trip.travelers).toLocaleString()}
                </div>
                <div className="text-xs text-slate-400 mt-1">
                  Available for booking in Booking Management tab
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      ))}

      <Card className="border-slate-200 bg-slate-50">
        <CardContent className="p-4">
          <div className="text-center text-sm text-slate-600">
            <p className="mb-2">
              💡 <strong>Travel Tip:</strong>
            </p>
            <p>
              {trip.transportation_preference === "public"
                ? "Public transport is cost-effective and lets you experience local life. Book train tickets 2-4 months in advance."
                : trip.transportation_preference === "private"
                ? "Private transport offers convenience and flexibility. Consider booking car rentals early for better rates."
                : "Mix of transport options gives you the best of both worlds - savings and comfort where needed."}
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
