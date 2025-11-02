import React, { useState, useEffect } from "react";
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
  Loader2,
} from "lucide-react";
import { useLanguage } from "../language/LanguageProvider";
import { useTranslation } from "../../hooks/useTranslation";

export default function TransportDetails({
  trip,
  dailyItineraries,
  transportDetails: transportDetailsProp = null,
  loadingTransport: loadingTransportProp = false,
  errorTransport: errorTransportProp = null,
  travelDetails: travelDetailsProp = null,
  loadingTravel: loadingTravelProp = false,
  errorTravel: errorTravelProp = null,
}) {
  const { t } = useLanguage();
  const { translate } = useTranslation();
  const [translatedRecommendations, setTranslatedRecommendations] = useState(
    []
  );

  // Use props if provided, otherwise fallback to local state (for backwards compatibility)
  const transportDetails = transportDetailsProp;
  const travelDetails = travelDetailsProp;
  const loadingTransport = loadingTransportProp;
  const loadingTravel = loadingTravelProp;
  const errorTransport = errorTransportProp;
  const errorTravel = errorTravelProp;

  // Helper function to get icon based on transport type
  const getTransportIcon = (type) => {
    switch (type) {
      case "flight":
        return Plane;
      case "train":
        return Train;
      case "bus":
        return Bus;
      case "car_rental":
      case "car":
        return Car;
      default:
        return Bus;
    }
  };

  // Helper function to get color scheme based on transport type
  const getTransportColor = (type) => {
    switch (type) {
      case "flight":
        return {
          color: "bg-blue-500",
          lightColor: "bg-blue-50",
          borderColor: "border-blue-200",
        };
      case "train":
        return {
          color: "bg-green-500",
          lightColor: "bg-green-50",
          borderColor: "border-green-200",
        };
      case "bus":
        return {
          color: "bg-orange-500",
          lightColor: "bg-orange-50",
          borderColor: "border-orange-200",
        };
      case "car_rental":
      case "car":
        return {
          color: "bg-purple-500",
          lightColor: "bg-purple-50",
          borderColor: "border-purple-200",
        };
      case "taxi":
        return {
          color: "bg-indigo-500",
          lightColor: "bg-indigo-50",
          borderColor: "border-indigo-200",
        };
      case "public_transport":
        return {
          color: "bg-yellow-500",
          lightColor: "bg-yellow-50",
          borderColor: "border-yellow-200",
        };
      default:
        return {
          color: "bg-slate-500",
          lightColor: "bg-slate-50",
          borderColor: "border-slate-200",
        };
    }
  };

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

  const renderTransportCard = (transport, index) => {
    const Icon = getTransportIcon(transport.type);
    const colors = getTransportColor(transport.type);

    return (
      <Card
        key={index}
        className={`border ${colors.borderColor} ${colors.lightColor}`}
      >
        <CardHeader>
          <CardTitle className="flex items-center gap-3">
            <div
              className={`w-10 h-10 ${colors.color} rounded-full flex items-center justify-center`}
            >
              <Icon className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="text-lg font-semibold text-slate-800">
                {transport.title}
              </div>
              <div className="text-sm text-slate-500">{transport.provider}</div>
            </div>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="space-y-3">
              {transport.route && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <MapPin className="w-4 h-4" />
                  <span>{transport.route}</span>
                </div>
              )}
              {transport.duration && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Clock className="w-4 h-4" />
                  <span>{transport.duration}</span>
                </div>
              )}
              {(transport.cost_per_person ||
                transport.total_cost ||
                transport.daily_cost) && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <DollarSign className="w-4 h-4" />
                  <span>
                    {transport.cost_per_person
                      ? `₹${transport.cost_per_person.toLocaleString()} per person`
                      : transport.total_cost
                      ? `₹${transport.total_cost.toLocaleString()} total`
                      : `₹${transport.daily_cost.toLocaleString()} per day`}
                  </span>
                </div>
              )}
              {transport.coverage && (
                <div className="text-xs text-slate-500">
                  Coverage: {transport.coverage}
                </div>
              )}
            </div>

            <div className="space-y-3">
              {transport.departure_time && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Calendar className="w-4 h-4" />
                  <span>Departure: {transport.departure_time}</span>
                </div>
              )}
              {transport.arrival_time && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <ArrowRight className="w-4 h-4" />
                  <span>Arrival: {transport.arrival_time}</span>
                </div>
              )}
              {(transport.class || transport.bookingClass) && (
                <div className="flex items-center gap-2 text-sm text-slate-600">
                  <Luggage className="w-4 h-4" />
                  <span>
                    Class: {transport.class || transport.bookingClass}
                  </span>
                </div>
              )}
              {transport.availability && (
                <div className="text-xs text-slate-500">
                  Available: {transport.availability}
                </div>
              )}
            </div>
          </div>

          {transport.description && (
            <div className="text-sm text-slate-600">
              {transport.description}
            </div>
          )}

          {transport.features && transport.features.length > 0 && (
            <div className="flex flex-wrap gap-2">
              {transport.features.map((feature, idx) => (
                <Badge key={idx} variant="outline" className="text-xs">
                  {feature}
                </Badge>
              ))}
            </div>
          )}

          {transport.booking_info && (
            <div className="text-xs text-slate-500 italic">
              💡 {transport.booking_info}
            </div>
          )}

          <div className="pt-4 border-t border-slate-200">
            <div className="text-center">
              {transport.cost_per_person && trip?.travelers && (
                <div className="text-sm text-slate-500">
                  Total for {trip.travelers} travelers: ₹
                  {(
                    transport.cost_per_person * trip.travelers
                  ).toLocaleString()}
                </div>
              )}
              {transport.total_cost && (
                <div className="text-sm text-slate-500">
                  Total cost: ₹{transport.total_cost.toLocaleString()}
                </div>
              )}
              <div className="text-xs text-slate-400 mt-1">
                {t("bookingDescription") ||
                  "Available for booking in Booking Management tab"}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  };

  return (
    <div className="space-y-8">
      {/* Travel Details Section (Inter-city: Flights, Trains, Buses) */}
      <div>
        <div className="text-center mb-6">
          <h3 className="text-xl font-semibold text-slate-800 mb-2">
            Travel Details (To/From Destination)
          </h3>
          <Badge variant="outline" className="bg-blue-50 text-blue-700">
            Inter-City Travel
          </Badge>
        </div>

        {loadingTravel ? (
          <Card className="border-slate-200">
            <CardContent className="p-8 text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-slate-400" />
              <p className="text-slate-600">Loading travel details...</p>
            </CardContent>
          </Card>
        ) : errorTravel ? (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4 text-center text-red-600">
              {errorTravel}
            </CardContent>
          </Card>
        ) : travelDetails ? (
          <>
            {/* Outbound Options */}
            {travelDetails.outbound_options &&
              travelDetails.outbound_options.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-slate-700 mb-4">
                    Outbound Journey
                  </h4>
                  <div className="space-y-4">
                    {travelDetails.outbound_options.map((option, index) =>
                      renderTransportCard(option, `outbound-${index}`)
                    )}
                  </div>
                </div>
              )}

            {/* Return Options */}
            {travelDetails.return_options &&
              travelDetails.return_options.length > 0 && (
                <div className="mb-6">
                  <h4 className="text-lg font-semibold text-slate-700 mb-4">
                    Return Journey
                  </h4>
                  <div className="space-y-4">
                    {travelDetails.return_options.map((option, index) =>
                      renderTransportCard(option, `return-${index}`)
                    )}
                  </div>
                </div>
              )}

            {/* Travel Tips */}
            {travelDetails.tips && travelDetails.tips.length > 0 && (
              <Card className="border-blue-200 bg-blue-50">
                <CardContent className="p-4">
                  <div className="text-center text-sm text-blue-800">
                    <p className="mb-2 font-semibold">💡 Travel Tips:</p>
                    <ul className="list-disc list-inside space-y-1 text-left">
                      {travelDetails.tips.map((tip, idx) => (
                        <li key={idx}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        ) : null}
      </div>

      {/* Transport Details Section (Local/City Transport) */}
      <div>
        <div className="text-center mb-6">
          <h3 className="text-xl font-semibold text-slate-800 mb-2">
            Local Transport Details
          </h3>
          <Badge variant="outline" className="bg-purple-50 text-purple-700">
            {getPreferenceText(
              transportDetails?.transport_preference ||
                trip?.transportation_preference ||
                "mixed"
            )}
          </Badge>
        </div>

        {loadingTransport ? (
          <Card className="border-slate-200">
            <CardContent className="p-8 text-center">
              <Loader2 className="w-8 h-8 animate-spin mx-auto mb-4 text-slate-400" />
              <p className="text-slate-600">Loading transport details...</p>
            </CardContent>
          </Card>
        ) : errorTransport ? (
          <Card className="border-red-200 bg-red-50">
            <CardContent className="p-4 text-center text-red-600">
              {errorTransport}
            </CardContent>
          </Card>
        ) : transportDetails ? (
          <>
            {/* Transport Recommendations */}
            {transportDetails.recommendations &&
              transportDetails.recommendations.length > 0 && (
                <div className="space-y-4 mb-6">
                  {transportDetails.recommendations.map((rec, index) =>
                    renderTransportCard(rec, `transport-${index}`)
                  )}
                </div>
              )}

            {/* Transport Tips */}
            {transportDetails.tips && transportDetails.tips.length > 0 && (
              <Card className="border-purple-200 bg-purple-50">
                <CardContent className="p-4">
                  <div className="text-center text-sm text-purple-800">
                    <p className="mb-2 font-semibold">💡 Transport Tips:</p>
                    <ul className="list-disc list-inside space-y-1 text-left">
                      {transportDetails.tips.map((tip, idx) => (
                        <li key={idx}>{tip}</li>
                      ))}
                    </ul>
                  </div>
                </CardContent>
              </Card>
            )}
          </>
        ) : null}
      </div>
    </div>
  );
}
