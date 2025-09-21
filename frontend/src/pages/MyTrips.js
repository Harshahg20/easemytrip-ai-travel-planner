import React, { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { createPageUrl } from "../utils";
import { Trip } from "../entities/Trip";
import { Button } from "../components/ui/button";
import { Card, CardHeader, CardContent } from "../components/ui/card";
import { Badge } from "../components/ui/badge";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "../components/ui/alert-dialog";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../components/ui/dropdown-menu";
import {
  Plus,
  Plane,
  MapPin,
  CheckCircle,
  Package,
  DollarSign,
  Calendar,
  Clock,
  MoreVertical,
  Edit,
  Eye,
  Trash2,
  Users,
} from "lucide-react";
import { motion } from "framer-motion";
import TripDetailModal from "../components/my-trips/TripDetailModal";
import { useLanguage } from "../components/language/LanguageProvider";

const getStatusColor = (status) => {
  switch (status) {
    case "booked":
      return "bg-blue-100 text-blue-800 border-blue-200";
    case "completed":
      return "bg-green-100 text-green-800 border-green-200";
    case "draft":
    default:
      return "bg-slate-100 text-slate-800 border-slate-200";
  }
};

const getStatusIcon = (status) => {
  switch (status) {
    case "booked":
      return Package;
    case "completed":
      return CheckCircle;
    case "draft":
    default:
      return Edit;
  }
};

export default function MyTrips() {
  const navigate = useNavigate();
  const { t } = useLanguage();
  const [trips, setTrips] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedTrip, setSelectedTrip] = useState(null);
  const [showModal, setShowModal] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [tripToDelete, setTripToDelete] = useState(null);

  const fetchTrips = async () => {
    setLoading(true);
    try {
      const userTrips = await Trip.list("-created_date");
      setTrips(userTrips);
    } catch (err) {
      setError("Failed to load trips.");
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTrips();
  }, []);

  const handleTripClick = (trip) => {
    setSelectedTrip(trip);
    setShowModal(true);
  };

  const handleViewDetails = (trip) => {
    navigate(createPageUrl(`TripPlanner?trip_id=${trip.id}`));
  };

  const handleDeleteRequest = (trip) => {
    setTripToDelete(trip);
    setShowDeleteConfirm(true);
  };

  const handleDeleteConfirm = async () => {
    if (tripToDelete) {
      try {
        await Trip.delete(tripToDelete.id);
        setTrips(trips.filter((t) => t.id !== tripToDelete.id));
      } catch (err) {
        setError("Failed to delete trip.");
        console.error(err);
      } finally {
        setTripToDelete(null);
        setShowDeleteConfirm(false);
      }
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-center min-h-64">
            <div className="w-16 h-16 bg-gradient-to-r from-slate-400 to-slate-500 rounded-full flex items-center justify-center mx-auto mb-4 animate-pulse">
              <Plane className="w-8 h-8 text-white" />
            </div>
            <p className="text-slate-600">{t("loadingTrips")}</p>
          </div>
        </div>
      </div>
    );
  }

  const tripDurationText = (trip) => {
    if (!trip.start_date || !trip.end_date) return "";
    const duration =
      Math.ceil(
        (new Date(trip.end_date) - new Date(trip.start_date)) /
          (1000 * 60 * 60 * 24)
      ) + 1;
    return `${duration} ${t("days")}`;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl lg:text-4xl font-bold text-slate-800 mb-2">
              {t("myTripsTitle")}
            </h1>
            <p className="text-slate-600">{t("manageAdventures")}</p>
          </div>
          <Button
            onClick={() => navigate(createPageUrl("TripForm"))}
            className="bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800 shadow-lg hover:shadow-xl transition-all duration-300"
          >
            <Plus className="w-5 h-5 mr-2" />
            {t("planNewTrip")}
          </Button>
        </div>

        {/* Stats Cards */}
        {trips.length > 0 && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-blue-500 to-blue-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <MapPin className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-slate-800">
                  {trips.length}
                </div>
                <div className="text-sm text-slate-600">{t("totalTrips")}</div>
              </CardContent>
            </Card>
            <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-green-500 to-green-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <CheckCircle className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-slate-800">
                  {trips.filter((t) => t.status === "completed").length}
                </div>
                <div className="text-sm text-slate-600">{t("completed")}</div>
              </CardContent>
            </Card>
            <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-purple-500 to-purple-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <Package className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-slate-800">
                  {trips.filter((t) => t.status === "booked").length}
                </div>
                <div className="text-sm text-slate-600">{t("booked")}</div>
              </CardContent>
            </Card>
            <Card className="bg-white/70 backdrop-blur-sm border-0 shadow-lg">
              <CardContent className="p-6 text-center">
                <div className="w-12 h-12 bg-gradient-to-r from-amber-500 to-amber-600 rounded-full flex items-center justify-center mx-auto mb-3">
                  <DollarSign className="w-6 h-6 text-white" />
                </div>
                <div className="text-2xl font-bold text-slate-800">
                  ₹
                  {trips
                    .reduce((sum, trip) => sum + (trip.total_budget || 0), 0)
                    .toLocaleString()}
                </div>
                <div className="text-sm text-slate-600">{t("budget")}</div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* Trips Grid */}
        {trips.length === 0 ? (
          <div className="text-center py-16">
            <div className="w-24 h-24 bg-gradient-to-r from-slate-200 to-slate-300 rounded-full flex items-center justify-center mx-auto mb-6">
              <Plane className="w-12 h-12 text-slate-500" />
            </div>
            <h3 className="text-2xl font-bold text-slate-800 mb-3">
              {t("noTripsYet")}
            </h3>
            <p className="text-slate-600 mb-8 max-w-md mx-auto">
              {t("startPlanning")}
            </p>
            <Button
              onClick={() => navigate(createPageUrl("TripForm"))}
              className="bg-gradient-to-r from-slate-600 to-slate-700 hover:from-slate-700 hover:to-slate-800"
            >
              <Plus className="w-5 h-5 mr-2" />
              {t("planFirstTrip")}
            </Button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {trips.map((trip, index) => {
              const StatusIcon = getStatusIcon(trip.status);
              const tripDuration = tripDurationText(trip);

              return (
                <motion.div
                  key={trip.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: index * 0.1 }}
                  className="h-full"
                >
                  <Card className="group bg-white/80 backdrop-blur-sm border-0 shadow-lg hover:shadow-2xl transition-all duration-300 h-full flex flex-col">
                    <CardContent className="p-6 flex flex-col h-full">
                      {/* Trip Header */}
                      <div className="flex items-start justify-between mb-4">
                        <div className="flex-1 pr-4">
                          <h3
                            className="text-xl font-bold text-slate-800 mb-2 group-hover:text-slate-900 line-clamp-2 cursor-pointer"
                            onClick={() => handleTripClick(trip)}
                          >
                            {trip.destination}
                          </h3>
                          <div className="flex items-center gap-4 text-sm text-slate-600">
                            <div className="flex items-center gap-1">
                              <Calendar className="w-4 h-4 flex-shrink-0" />
                              <span className="truncate">
                                {trip.start_date
                                  ? new Date(
                                      trip.start_date
                                    ).toLocaleDateString()
                                  : t("dateTBD")}
                              </span>
                            </div>
                            {tripDuration && (
                              <div className="flex items-center gap-1">
                                <Clock className="w-4 h-4 flex-shrink-0" />
                                <span>{tripDuration}</span>
                              </div>
                            )}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            className={`${getStatusColor(
                              trip.status
                            )} border flex items-center gap-1 flex-shrink-0`}
                          >
                            <StatusIcon className="w-3 h-3" />
                            <span className="text-xs">{trip.status}</span>
                          </Badge>
                          <DropdownMenu>
                            <DropdownMenuTrigger asChild>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="h-8 w-8 flex-shrink-0 hover:bg-slate-100"
                              >
                                <MoreVertical className="w-4 h-4" />
                              </Button>
                            </DropdownMenuTrigger>
                            <DropdownMenuContent align="end">
                              <DropdownMenuItem
                                onClick={() => handleViewDetails(trip)}
                              >
                                <Edit className="mr-2 h-4 w-4" />
                                <span>{t("viewEditDetails")}</span>
                              </DropdownMenuItem>
                              <DropdownMenuItem
                                onClick={() => handleTripClick(trip)}
                              >
                                <Eye className="mr-2 h-4 w-4" />
                                <span>{t("quickView")}</span>
                              </DropdownMenuItem>
                              <DropdownMenuSeparator />
                              <DropdownMenuItem
                                className="text-red-600 focus:text-red-600 focus:bg-red-50"
                                onClick={() => handleDeleteRequest(trip)}
                              >
                                <Trash2 className="mr-2 h-4 w-4" />
                                <span>{t("deleteTrip")}</span>
                              </DropdownMenuItem>
                            </DropdownMenuContent>
                          </DropdownMenu>
                        </div>
                      </div>

                      {/* Trip Details */}
                      <div className="grid grid-cols-2 gap-4 mb-4">
                        <div className="flex items-center gap-2 text-slate-600">
                          <Users className="w-4 h-4 flex-shrink-0" />
                          <span className="text-sm truncate">
                            {trip.travelers}{" "}
                            {trip.travelers === 1
                              ? t("traveler")
                              : t("travelers")}
                          </span>
                        </div>
                        <div className="flex items-center gap-2 text-slate-600">
                          <DollarSign className="w-4 h-4 flex-shrink-0" />
                          <span className="text-sm font-medium truncate">
                            ₹{trip.total_budget?.toLocaleString() || "0"}
                          </span>
                        </div>
                      </div>

                      {/* Themes/Interests - Fixed height section */}
                      <div className="mb-6 min-h-[60px] flex flex-col justify-start">
                        {trip.themes && trip.themes.length > 0 ? (
                          <div className="flex flex-wrap gap-2">
                            {trip.themes.slice(0, 3).map((theme, idx) => (
                              <Badge
                                key={idx}
                                variant="secondary"
                                className="text-xs bg-slate-100 text-slate-700"
                              >
                                {t(`theme_${theme}`)}
                              </Badge>
                            ))}
                            {trip.themes.length > 3 && (
                              <Badge
                                variant="secondary"
                                className="text-xs bg-slate-100 text-slate-700"
                              >
                                +{trip.themes.length - 3} more
                              </Badge>
                            )}
                          </div>
                        ) : (
                          <div className="text-xs text-slate-400 italic">
                            {t("noThemesSelected")}
                          </div>
                        )}
                      </div>

                      {/* Spacer to push buttons to bottom */}
                      <div className="flex-1"></div>

                      {/* Action Buttons - Always at bottom with proper alignment */}
                      <div className="flex gap-3 pt-4 border-t border-slate-100 mt-auto">
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1 text-slate-600 border-slate-200 hover:bg-slate-50 hover:border-slate-300 transition-all duration-200"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleTripClick(trip);
                          }}
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          {t("quickView")}
                        </Button>
                        <Button
                          size="sm"
                          className="flex-1 bg-slate-700 hover:bg-slate-800 text-white transition-all duration-200 shadow-sm hover:shadow-md"
                          onClick={(e) => {
                            e.stopPropagation();
                            handleViewDetails(trip);
                          }}
                        >
                          <Edit className="w-4 h-4 mr-2" />
                          {t("details")}
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                </motion.div>
              );
            })}
          </div>
        )}

        {/* Trip Detail Modal */}
        <TripDetailModal
          trip={selectedTrip}
          isOpen={showModal}
          onClose={() => setShowModal(false)}
          onViewDetails={handleViewDetails}
        />

        {/* Delete Confirmation Dialog */}
        <AlertDialog
          open={showDeleteConfirm}
          onOpenChange={setShowDeleteConfirm}
        >
          <AlertDialogContent>
            <AlertDialogHeader>
              <AlertDialogTitle>{t("deleteConfirmTitle")}</AlertDialogTitle>
              <AlertDialogDescription>
                {t("deleteConfirmDescription")}
              </AlertDialogDescription>
            </AlertDialogHeader>
            <AlertDialogFooter>
              <AlertDialogCancel>{t("cancel")}</AlertDialogCancel>
              <AlertDialogAction
                onClick={handleDeleteConfirm}
                className="bg-red-600 hover:bg-red-700"
              >
                {t("delete")}
              </AlertDialogAction>
            </AlertDialogFooter>
          </AlertDialogContent>
        </AlertDialog>
      </div>
    </div>
  );
}
