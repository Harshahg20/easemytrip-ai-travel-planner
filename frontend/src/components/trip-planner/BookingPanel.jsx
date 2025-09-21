import React, { useState } from "react";
import { Trip } from "../../entities/Trip";
import { Button } from "../ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Badge } from "../ui/badge";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../ui/dialog";
import {
  Loader2,
  Plane,
  BedDouble,
  Ticket,
  CheckCircle,
  PartyPopper,
  Calendar,
  Users,
  DollarSign,
  Train,
  Car,
  Bus,
} from "lucide-react";
import { useLanguage } from "../language/LanguageProvider";
import { motion } from "framer-motion";

export default function BookingPanel({ trip, onBookingComplete }) {
  const { t } = useLanguage();
  const [isBooking, setIsBooking] = useState(false);
  const [showSuccessModal, setShowSuccessModal] = useState(false);
  const [bookingDetails, setBookingDetails] = useState(null);

  const handleBookTrip = async () => {
    setIsBooking(true);
    try {
      // Simulate API call to EaseMyTrip with realistic delay
      await new Promise((resolve) => setTimeout(resolve, 3000));

      const bookingReference = `EMT-${Date.now().toString().slice(-6)}`;
      const updatedTrip = await Trip.update(trip.id, {
        status: "booked",
        booking_reference: bookingReference,
      });

      // Set booking details for success modal
      setBookingDetails({
        reference: bookingReference,
        destination: trip.destination,
        travelers: trip.travelers,
        dates: `${new Date(trip.start_date).toLocaleDateString()} - ${new Date(
          trip.end_date
        ).toLocaleDateString()}`,
        totalCost:
          trip.selected_plan?.total_estimated_cost || trip.total_budget,
      });

      setShowSuccessModal(true);
    } catch (error) {
      console.error("Booking failed:", error);
      alert("Booking failed. Please try again.");
    } finally {
      setIsBooking(false);
    }
  };

  const handleSuccessModalClose = () => {
    setShowSuccessModal(false);
    // Reload the trip data to show updated status
    if (onBookingComplete) {
      onBookingComplete();
    }
  };

  const totalCost =
    trip.selected_plan?.total_estimated_cost || trip.total_budget;
  const flightCost = Math.round(totalCost * 0.25);
  const hotelCost = Math.round(totalCost * 0.4);
  const activityCost = Math.round(totalCost * 0.2);
  const transportCost = Math.round(totalCost * 0.15);

  // Generate transport options for booking
  const getTransportOptions = () => {
    const preference = trip.transportation_preference || "mixed";
    const options = [];

    if (preference === "private" || preference === "mixed") {
      options.push({
        type: "flight",
        title: "Flights",
        icon: Plane,
        cost: flightCost,
        color: "bg-blue-500",
        lightColor: "bg-blue-50",
      });
    }

    if (preference === "public" || preference === "mixed") {
      options.push({
        type: "train",
        title: "Train Tickets",
        icon: Train,
        cost: Math.round(totalCost * 0.15),
        color: "bg-green-500",
        lightColor: "bg-green-50",
      });
    }

    options.push({
      type: "local",
      title: preference === "private" ? "Car Rental" : "Local Transport",
      icon: preference === "private" ? Car : Bus,
      cost:
        preference === "private"
          ? Math.round(totalCost * 0.2)
          : Math.round(totalCost * 0.05),
      color: preference === "private" ? "bg-purple-500" : "bg-orange-500",
      lightColor: preference === "private" ? "bg-purple-50" : "bg-orange-50",
    });

    return options;
  };

  const transportOptions = getTransportOptions();

  if (trip.status === "booked" || trip.status === "completed") {
    return (
      <Card className="border-green-200 bg-gradient-to-br from-green-50 to-emerald-50 shadow-sm">
        <CardHeader>
          <CardTitle className="flex items-center gap-3 text-green-800">
            <div className="w-8 h-8 bg-green-100 rounded-full flex items-center justify-center">
              <CheckCircle className="w-5 h-5 text-green-600" />
            </div>
            {t("tripBookedSuccessfully")}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="bg-white/70 rounded-lg p-4 border border-green-200">
            <div className="text-sm font-medium text-green-700 mb-2">
              {t("bookingReference")}:
            </div>
            <div className="font-mono text-lg text-green-900 bg-green-50 px-3 py-2 rounded border">
              {trip.booking_reference}
            </div>
          </div>

          <div className="flex items-center justify-between">
            <Badge className="bg-green-100 text-green-800 border-green-200 px-3 py-1">
              <CheckCircle className="w-4 h-4 mr-2" />
              {t("status")}: {t(trip.status)}
            </Badge>
            <div className="text-sm text-green-700">
              Powered by <span className="font-semibold">EaseMyTrip</span>
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <>
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span className="flex items-center gap-2">
              {t("bookingManagement")}
            </span>
            <Badge
              variant="outline"
              className="bg-amber-50 text-amber-700 border-amber-200"
            >
              {t("status")}: {t(trip.status || "draft")}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-200">
            <p className="text-sm text-slate-700 leading-relaxed">
              Ready to make it official? Book your flights, hotels, transport
              and activities in one click. We'll handle the rest with our
              partner,{" "}
              <span className="font-semibold text-blue-700">EaseMyTrip</span>.
            </p>
          </div>

          <div className="space-y-4">
            {/* Transport Options */}
            {transportOptions.map((transport, index) => (
              <div
                key={index}
                className={`flex justify-between items-center p-4 ${transport.lightColor} rounded-lg border`}
              >
                <div className="flex items-center gap-3">
                  <div
                    className={`w-10 h-10 ${transport.color} rounded-full flex items-center justify-center`}
                  >
                    <transport.icon className="w-5 h-5 text-white" />
                  </div>
                  <span className="font-semibold text-slate-800">
                    {transport.title}
                  </span>
                </div>
                <div className="text-right">
                  <div className="font-bold text-slate-900">
                    ₹{transport.cost.toLocaleString()}
                  </div>
                  <div className="text-xs text-slate-500">
                    {t("estimatedCost")}
                  </div>
                </div>
              </div>
            ))}

            {/* Hotels */}
            <div className="flex justify-between items-center p-4 bg-gradient-to-r from-purple-50 to-pink-50 rounded-lg border border-purple-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-purple-500 rounded-full flex items-center justify-center">
                  <BedDouble className="w-5 h-5 text-white" />
                </div>
                <span className="font-semibold text-slate-800">
                  {t("hotels")}
                </span>
              </div>
              <div className="text-right">
                <div className="font-bold text-slate-900">
                  ₹{hotelCost.toLocaleString()}
                </div>
                <div className="text-xs text-slate-500">
                  {t("estimatedCost")}
                </div>
              </div>
            </div>

            {/* Activities */}
            <div className="flex justify-between items-center p-4 bg-gradient-to-r from-emerald-50 to-green-50 rounded-lg border border-emerald-100">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-emerald-500 rounded-full flex items-center justify-center">
                  <Ticket className="w-5 h-5 text-white" />
                </div>
                <span className="font-semibold text-slate-800">
                  {t("activities")}
                </span>
              </div>
              <div className="text-right">
                <div className="font-bold text-slate-900">
                  ₹{activityCost.toLocaleString()}
                </div>
                <div className="text-xs text-slate-500">
                  {t("estimatedCost")}
                </div>
              </div>
            </div>
          </div>

          {/* Total and Book Button */}
          <div className="pt-6 border-t border-slate-200">
            <div className="bg-slate-50 rounded-lg p-4 mb-4 border">
              <div className="flex justify-between items-center">
                <span className="text-lg font-semibold text-slate-800">
                  Total Cost:
                </span>
                <span className="text-2xl font-bold text-slate-900">
                  ₹{totalCost.toLocaleString()}
                </span>
              </div>
            </div>

            <div className="text-center">
              <Button
                onClick={handleBookTrip}
                disabled={isBooking}
                className="w-full max-w-xs mx-auto bg-gradient-to-r from-blue-600 to-blue-700 hover:from-blue-700 hover:to-blue-800 text-white shadow-lg hover:shadow-xl transition-all duration-300 h-12"
              >
                {isBooking ? (
                  <>
                    <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                    {t("bookingYourTrip")}
                  </>
                ) : (
                  <>
                    <CheckCircle className="mr-2 h-5 w-5" />
                    {t("bookNow")}
                  </>
                )}
              </Button>
              <p className="text-xs text-slate-500 mt-3">
                Secure booking powered by{" "}
                <span className="font-medium">EaseMyTrip</span>
              </p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Success Modal */}
      <Dialog open={showSuccessModal} onOpenChange={setShowSuccessModal}>
        <DialogContent className="max-w-md bg-gradient-to-br from-white to-green-50 border-green-200">
          <DialogHeader>
            <div className="text-center">
              <motion.div
                initial={{ scale: 0 }}
                animate={{ scale: 1 }}
                transition={{ type: "spring", duration: 0.6 }}
                className="w-16 h-16 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-4"
              >
                <PartyPopper className="w-8 h-8 text-white" />
              </motion.div>
              <DialogTitle className="text-2xl font-bold text-green-800 mb-2">
                Booking Confirmed! 🎉
              </DialogTitle>
            </div>
          </DialogHeader>

          {bookingDetails && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.3 }}
              className="space-y-4"
            >
              <div className="bg-white rounded-lg p-4 border border-green-200 shadow-sm">
                <div className="text-center mb-4">
                  <h3 className="font-bold text-slate-800 text-lg">
                    Your trip is all set!
                  </h3>
                  <p className="text-slate-600 text-sm">
                    Get ready for an amazing adventure.
                  </p>
                </div>

                <div className="space-y-3 text-sm">
                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Calendar className="w-4 h-4" />
                      <span>Booking Reference:</span>
                    </div>
                    <span className="font-mono font-bold text-green-700">
                      {bookingDetails.reference}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2 text-slate-600">
                      <Users className="w-4 h-4" />
                      <span>Travelers:</span>
                    </div>
                    <span className="font-semibold">
                      {bookingDetails.travelers}
                    </span>
                  </div>

                  <div className="flex justify-between items-center">
                    <div className="flex items-center gap-2 text-slate-600">
                      <DollarSign className="w-4 h-4" />
                      <span>Total Cost:</span>
                    </div>
                    <span className="font-bold text-green-700">
                      ₹{bookingDetails.totalCost.toLocaleString()}
                    </span>
                  </div>
                </div>
              </div>

              <div className="text-center">
                <Button
                  onClick={handleSuccessModalClose}
                  className="w-full bg-green-600 hover:bg-green-700 text-white"
                >
                  View Trip Details
                </Button>
                <p className="text-xs text-slate-500 mt-2">
                  A confirmation email will be sent shortly
                </p>
              </div>
            </motion.div>
          )}
        </DialogContent>
      </Dialog>
    </>
  );
}
