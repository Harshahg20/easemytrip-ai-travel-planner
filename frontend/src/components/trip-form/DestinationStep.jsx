import React from "react";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { MapPin, Sparkles } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "../language/LanguageProvider";

export default function DestinationStep({ formData, updateFormData }) {
  const { t } = useLanguage();

  const popularDestinations = [
    { key: "rajasthan", emoji: "🏰" },
    { key: "kerala", emoji: "🌴" },
    { key: "goa", emoji: "🏖️" },
    { key: "himachal", emoji: "🏔️" },
    { key: "karnataka", emoji: "🌸" },
    { key: "tamil_nadu", emoji: "🏛️" },
    { key: "maharashtra", emoji: "🌆" },
    { key: "west_bengal", emoji: "🎭" },
  ];

  const getDestinationName = (key) => {
    switch (key) {
      case "rajasthan":
        return "Rajasthan (Jaipur, Udaipur, Jodhpur)";
      case "kerala":
        return "Kerala (Kochi, Munnar, Alleppey)";
      case "goa":
        return "Goa";
      case "himachal":
        return "Himachal Pradesh (Shimla, Manali)";
      case "karnataka":
        return "Karnataka (Bangalore, Mysore, Coorg)";
      case "tamil_nadu":
        return "Tamil Nadu (Chennai, Pondicherry)";
      case "maharashtra":
        return "Maharashtra (Mumbai, Pune, Aurangabad)";
      case "west_bengal":
        return "West Bengal (Kolkata, Darjeeling)";
      default:
        return "";
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <div className="text-center mb-8">
        <h3 className="text-3xl font-bold text-slate-800 mb-3">
          {t("whereToExplore")}
        </h3>
        <p className="text-slate-600 text-lg">{t("chooseDreamDestination")}</p>
      </div>

      <div className="max-w-md mx-auto space-y-6">
        {/* Destination Input */}
        <div>
          <Label
            htmlFor="destination"
            className="text-lg font-semibold text-slate-700 mb-3 block"
          >
            {t("destination")}
          </Label>
          <div className="relative">
            <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400" />
            <Input
              id="destination"
              placeholder={t("destinationPlaceholder")}
              value={formData.destination}
              onChange={(e) => updateFormData({ destination: e.target.value })}
              className="pl-12 h-14 text-lg border-2 border-slate-200 rounded-xl focus:border-slate-400 focus:ring-4 focus:ring-slate-100 transition-all duration-300"
            />
          </div>
          <p className="text-sm text-slate-500 mt-3 text-center">
            {t("destinationHelper")}
          </p>
        </div>
      </div>

      {/* Popular suggestions */}
      <div className="max-w-4xl mx-auto">
        <div className="flex items-center justify-center gap-2 mb-6">
          <Sparkles className="w-5 h-5 text-slate-500" />
          <p className="text-lg font-semibold text-slate-700">
            {t("popularIndianDestinations")}
          </p>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {popularDestinations.map((dest, index) => {
            const name = getDestinationName(dest.key);
            return (
              <motion.button
                key={dest.key}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.1 * index }}
                onClick={() => updateFormData({ destination: name })}
                className={`p-4 rounded-xl border-2 transition-all duration-300 text-center hover:shadow-md hover:scale-105 ${
                  formData.destination === name
                    ? "border-slate-500 bg-slate-50 shadow-md"
                    : "border-slate-200 hover:border-slate-300 bg-white"
                }`}
              >
                <div className="text-3xl mb-2">{dest.emoji}</div>
                <div className="font-semibold text-slate-800 text-sm mb-1">
                  {t(`dest_${dest.key}`)}
                </div>
                <div className="text-xs text-slate-500">
                  {t(`dest_${dest.key}_desc`)}
                </div>
              </motion.button>
            );
          })}
        </div>
      </div>
    </motion.div>
  );
}
