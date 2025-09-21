import React from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "../ui/dialog";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Card, CardContent } from "../ui/card";
import {
  MapPin,
  Calendar,
  DollarSign,
  Users,
  Clock,
  Plane,
  Home,
  Car,
  Heart,
  CheckCircle,
  Package,
  AlertCircle,
  Globe,
  FileText,
  ExternalLink,
  Edit, // Added Edit icon
} from "lucide-react";

export default function TripDetailModal({
  trip,
  isOpen,
  onClose,
  onViewDetails,
}) {
  if (!trip) return null;

  const tripDuration =
    trip.start_date && trip.end_date
      ? Math.ceil(
          (new Date(trip.end_date) - new Date(trip.start_date)) /
            (1000 * 60 * 60 * 24)
        ) + 1
      : 0;

  const getStatusColor = (status) => {
    switch (status) {
      case "completed":
        return "bg-green-100 text-green-700 border-green-200";
      case "booked":
        return "bg-blue-100 text-blue-700 border-blue-200";
      case "confirmed":
        return "bg-purple-100 text-purple-700 border-purple-200";
      default:
        return "bg-slate-100 text-slate-700 border-slate-200";
    }
  };

  const getStatusIcon = (status) => {
    switch (status) {
      case "completed":
        return CheckCircle;
      case "booked":
        return Package;
      case "confirmed":
        return CheckCircle;
      default:
        return AlertCircle;
    }
  };

  const StatusIcon = getStatusIcon(trip.status);

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-4xl max-h-[90vh] overflow-y-auto bg-gradient-to-br from-white to-slate-50">
        <DialogHeader className="pb-6 border-b border-slate-100">
          <div className="flex items-start justify-between">
            <div className="flex-1">
              <DialogTitle className="text-2xl font-bold text-slate-800 mb-3">
                {trip.destination}
              </DialogTitle>
              <div className="flex items-center gap-4 text-sm text-slate-600 mb-3">
                <div className="flex items-center gap-1">
                  <Calendar className="w-4 h-4" />
                  <span>
                    {trip.start_date && trip.end_date
                      ? `${new Date(
                          trip.start_date
                        ).toLocaleDateString()} - ${new Date(
                          trip.end_date
                        ).toLocaleDateString()}`
                      : "Dates to be confirmed"}
                  </span>
                </div>
                {tripDuration > 0 && (
                  <div className="flex items-center gap-1">
                    <Clock className="w-4 h-4" />
                    <span>{tripDuration} days</span>
                  </div>
                )}
              </div>
            </div>
            <Badge
              className={`${getStatusColor(
                trip.status
              )} border flex items-center gap-2 text-sm px-3 py-1`}
            >
              <StatusIcon className="w-4 h-4" />
              {trip.status}
            </Badge>
          </div>
        </DialogHeader>

        <div className="space-y-6 pt-6">
          {/* Key Details Grid */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <div className="w-10 h-10 bg-gradient-to-r from-blue-500 to-blue-600 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Users className="w-5 h-5 text-white" />
                </div>
                <div className="text-lg font-bold text-slate-800">
                  {trip.travelers}
                </div>
                <div className="text-xs text-slate-600">Travelers</div>
              </CardContent>
            </Card>

            <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <div className="w-10 h-10 bg-gradient-to-r from-emerald-500 to-emerald-600 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <DollarSign className="w-5 h-5 text-white" />
                </div>
                <div className="text-lg font-bold text-slate-800">
                  ₹{trip.total_budget?.toLocaleString() || "0"}
                </div>
                <div className="text-xs text-slate-600">Budget</div>
              </CardContent>
            </Card>

            <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <div className="w-10 h-10 bg-gradient-to-r from-purple-500 to-purple-600 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Home className="w-5 h-5 text-white" />
                </div>
                <div className="text-lg font-bold text-slate-800 capitalize">
                  {trip.accommodation_preference || "N/A"}
                </div>
                <div className="text-xs text-slate-600">Stay</div>
              </CardContent>
            </Card>

            <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
              <CardContent className="p-4 text-center">
                <div className="w-10 h-10 bg-gradient-to-r from-orange-500 to-orange-600 rounded-lg flex items-center justify-center mx-auto mb-2">
                  <Car className="w-5 h-5 text-white" />
                </div>
                <div className="text-lg font-bold text-slate-800 capitalize">
                  {trip.transportation_preference || "N/A"}
                </div>
                <div className="text-xs text-slate-600">Transport</div>
              </CardContent>
            </Card>
          </div>

          {/* Travel Themes */}
          {trip.themes && trip.themes.length > 0 && (
            <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Heart className="w-5 h-5 text-red-500" />
                  <h3 className="text-lg font-semibold text-slate-800">
                    Travel Interests
                  </h3>
                </div>
                <div className="flex flex-wrap gap-2">
                  {trip.themes.map((theme, index) => (
                    <Badge
                      key={index}
                      variant="secondary"
                      className="bg-gradient-to-r from-slate-100 to-slate-200 text-slate-700 px-3 py-1"
                    >
                      {theme.replace("_", " ")}
                    </Badge>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Language & Special Requirements */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {trip.language && (
              <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
                <CardContent className="p-6">
                  <div className="flex items-center gap-2 mb-3">
                    <Globe className="w-5 h-5 text-blue-500" />
                    <h3 className="text-lg font-semibold text-slate-800">
                      Language Preference
                    </h3>
                  </div>
                  <p className="text-slate-600 capitalize">
                    {trip.language === "hindi" ? "Hindi (हिंदी)" : "English"}
                  </p>
                </CardContent>
              </Card>
            )}

            {trip.special_requirements && (
              <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-sm">
                <CardContent className="p-6">
                  <div className="flex items-center gap-2 mb-3">
                    <FileText className="w-5 h-5 text-purple-500" />
                    <h3 className="text-lg font-semibold text-slate-800">
                      Special Requirements
                    </h3>
                  </div>
                  <p className="text-slate-600 text-sm leading-relaxed">
                    {trip.special_requirements}
                  </p>
                </CardContent>
              </Card>
            )}
          </div>

          {/* Booking Information */}
          {(trip.booking_reference || trip.total_cost) && (
            <Card className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 shadow-sm">
              <CardContent className="p-6">
                <div className="flex items-center gap-2 mb-4">
                  <Package className="w-5 h-5 text-blue-600" />
                  <h3 className="text-lg font-semibold text-slate-800">
                    Booking Details
                  </h3>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {trip.booking_reference && (
                    <div>
                      <div className="text-sm font-medium text-slate-700 mb-1">
                        Booking Reference
                      </div>
                      <div className="text-blue-700 font-mono text-sm">
                        {trip.booking_reference}
                      </div>
                    </div>
                  )}
                  {trip.total_cost && (
                    <div>
                      <div className="text-sm font-medium text-slate-700 mb-1">
                        Total Cost
                      </div>
                      <div className="text-green-700 font-semibold">
                        ₹{trip.total_cost.toLocaleString()}
                      </div>
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4 border-t border-slate-200">
            <Button
              variant="outline"
              onClick={onClose}
              className="flex-1 border-slate-300 text-slate-700 hover:bg-slate-50"
            >
              Close
            </Button>
            <Button
              onClick={() => {
                onViewDetails(trip);
                onClose();
              }}
              className="flex-1 bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 text-white shadow-lg hover:shadow-xl transition-all duration-300"
            >
              <Edit className="w-4 h-4 mr-2" />
              View Full Itinerary
            </Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
