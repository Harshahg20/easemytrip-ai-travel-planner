import React from "react";
import { Button } from "../ui/button";
import { Users, Minus, Plus, Heart } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "../language/LanguageProvider";

export default function TravelersStep({ formData, updateFormData }) {
  const { t } = useLanguage();

  const updateTravelers = (count) => {
    // Ensure the count is at least 1 and not more than 20
    const newCount = Math.max(1, Math.min(20, count));
    updateFormData({ travelers: newCount });
  };

  const quickSelectOptions = [
    {
      count: 1,
      label: t("soloAdventure"),
      emoji: "🎒",
      description: t("justMe"),
    },
    {
      count: 2,
      label: t("romanticGetaway"),
      emoji: "💕",
      description: t("mePartner"),
    },
    {
      count: 4,
      label: t("familyFun"),
      emoji: "👨‍👩‍👧‍👦",
      description: t("familyTrip"),
    },
    {
      count: 6,
      label: t("groupAdventure"),
      emoji: "👥",
      description: t("friendsTrip"),
    },
    {
      count: 8,
      label: t("largeGroup"),
      emoji: "🎉",
      description: t("bigCelebration"),
    },
  ];

  const travelerCount = formData.travelers || 1; // Default to 1 if not set

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <div className="text-center mb-8">
        <h3 className="text-3xl font-bold text-gray-900 mb-3">
          {t("whosJoining")}
        </h3>
        <p className="text-gray-600 text-lg">{t("howManyTravelers")}</p>
      </div>

      <div className="max-w-lg mx-auto space-y-8">
        {/* Counter */}
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ delay: 0.3 }}
          className="text-center"
        >
          <div className="inline-flex items-center gap-6 bg-gradient-to-r from-gray-50 to-orange-50 rounded-3xl p-6 border-2 border-orange-100 shadow-sm">
            <Button
              variant="outline"
              size="icon"
              onClick={() => updateTravelers(travelerCount - 1)}
              disabled={travelerCount <= 1}
              className="rounded-full h-14 w-14 border-2 hover:bg-orange-50 hover:border-orange-300 transition-all duration-300"
            >
              <Minus className="w-5 h-5" />
            </Button>

            <div className="text-center min-w-[120px]">
              <div className="text-4xl font-bold text-gray-900 mb-1">
                {travelerCount}
              </div>
              <div className="text-sm text-gray-600">
                {travelerCount === 1 ? t("traveler") : t("travelers")}
              </div>
            </div>

            <Button
              variant="outline"
              size="icon"
              onClick={() => updateTravelers(travelerCount + 1)}
              disabled={travelerCount >= 20}
              className="rounded-full h-14 w-14 border-2 hover:bg-orange-50 hover:border-orange-300 transition-all duration-300"
            >
              <Plus className="w-5 h-5" />
            </Button>
          </div>
        </motion.div>

        {/* Quick select options */}
        <div>
          <div className="flex items-center justify-center gap-2 mb-6">
            <Heart className="w-5 h-5 text-red-500" />
            <p className="text-lg font-semibold text-gray-700">
              {t("quickSelect")}
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {quickSelectOptions.map((option, index) => (
              <motion.button
                key={option.count}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                onClick={() => updateTravelers(option.count)}
                className={`p-4 rounded-xl border-2 transition-all duration-300 text-left hover:shadow-md ${
                  travelerCount === option.count
                    ? "border-orange-500 bg-orange-50 shadow-md scale-105"
                    : "border-gray-200 hover:border-orange-300 bg-white hover:scale-102"
                }`}
              >
                <div className="flex items-center gap-3 mb-2">
                  <span className="text-2xl">{option.emoji}</span>
                  <span className="font-semibold text-gray-900">
                    {option.label}
                  </span>
                </div>
                <p className="text-sm text-gray-600">{option.description}</p>
                <div className="text-xs text-orange-600 font-medium mt-1">
                  {option.count}{" "}
                  {option.count === 1 ? t("person") : t("people")}
                </div>
              </motion.button>
            ))}
          </div>
        </div>
      </div>
    </motion.div>
  );
}
