import React from "react";
import { Label } from "../ui/label";
import { Textarea } from "../ui/textarea";
import { Card, CardContent } from "../ui/card";
import { Home, Car, MessageCircle } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "../language/LanguageProvider";

export default function PreferencesStep({ formData, updateFormData }) {
  const { t } = useLanguage();

  const accommodationOptions = [
    {
      id: "budget",
      label: t("budget_acco"),
      description: t("budget_acco_desc"),
      icon: "💰",
      gradient: "from-green-400 to-green-500",
    },
    {
      id: "mid-range",
      label: t("midRange_acco"),
      description: t("midRange_acco_desc"),
      icon: "🏨",
      gradient: "from-blue-400 to-blue-500",
    },
    {
      id: "luxury",
      label: t("luxury_acco"),
      description: t("luxury_acco_desc"),
      icon: "✨",
      gradient: "from-purple-400 to-purple-500",
    },
  ];

  const transportOptions = [
    {
      id: "public",
      label: t("publicTransport"),
      description: t("public_transport_desc"),
      icon: "🚇",
      gradient: "from-green-400 to-green-500",
    },
    {
      id: "private",
      label: t("privateTransport"),
      description: t("private_transport_desc"),
      icon: "🚗",
      gradient: "from-red-400 to-red-500",
    },
    {
      id: "mixed",
      label: t("mixed"),
      description: t("mixed_desc"),
      icon: "🚌",
      gradient: "from-orange-400 to-orange-500",
    },
  ];

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <div className="text-center mb-8">
        <h3 className="text-3xl font-bold text-gray-900 mb-3">
          {t("finalTouches")}
        </h3>
        <p className="text-gray-600 text-lg">{t("tellUsPreferences")}</p>
      </div>

      <div className="max-w-4xl mx-auto space-y-10">
        {/* Accommodation Preference */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.3 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-gradient-to-r from-blue-500 to-purple-500 rounded-lg flex items-center justify-center">
              <Home className="w-5 h-5 text-white" />
            </div>
            <Label className="text-xl font-bold text-gray-900">
              {t("accommodationPref")}
            </Label>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {accommodationOptions.map((option, index) => (
              <motion.button
                key={option.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.4 + index * 0.1 }}
                onClick={() =>
                  updateFormData({ accommodation_preference: option.id })
                }
                className={`text-left p-6 rounded-2xl border-2 transition-all duration-300 hover:scale-105 ${
                  formData.accommodation_preference === option.id
                    ? "border-orange-500 bg-orange-50 shadow-lg scale-105"
                    : "border-gray-200 hover:border-gray-300 bg-white hover:shadow-md"
                }`}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className={`w-12 h-12 bg-gradient-to-r ${option.gradient} rounded-xl flex items-center justify-center text-2xl shadow-lg`}
                  >
                    {option.icon}
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900 text-lg">
                      {option.label}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {option.description}
                    </p>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Transportation Preference */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.5 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-gradient-to-r from-green-500 to-blue-500 rounded-lg flex items-center justify-center">
              <Car className="w-5 h-5 text-white" />
            </div>
            <Label className="text-xl font-bold text-gray-900">
              {t("transportationPref")}
            </Label>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {transportOptions.map((option, index) => (
              <motion.button
                key={option.id}
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: 0.6 + index * 0.1 }}
                onClick={() =>
                  updateFormData({ transportation_preference: option.id })
                }
                className={`text-left p-6 rounded-2xl border-2 transition-all duration-300 hover:scale-105 ${
                  formData.transportation_preference === option.id
                    ? "border-orange-500 bg-orange-50 shadow-lg scale-105"
                    : "border-gray-200 hover:border-gray-300 bg-white hover:shadow-md"
                }`}
              >
                <div className="flex items-center gap-3 mb-3">
                  <div
                    className={`w-12 h-12 bg-gradient-to-r ${option.gradient} rounded-xl flex items-center justify-center text-2xl shadow-lg`}
                  >
                    {option.icon}
                  </div>
                  <div>
                    <h4 className="font-bold text-gray-900 text-lg">
                      {option.label}
                    </h4>
                    <p className="text-sm text-gray-600">
                      {option.description}
                    </p>
                  </div>
                </div>
              </motion.button>
            ))}
          </div>
        </motion.div>

        {/* Special Requirements */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.8 }}
        >
          <div className="flex items-center gap-3 mb-6">
            <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
              <MessageCircle className="w-5 h-5 text-white" />
            </div>
            <Label
              htmlFor="special_requirements"
              className="text-xl font-bold text-gray-900"
            >
              {t("specialRequirements")}
            </Label>
          </div>
          <Card className="border-2 border-gray-200 hover:border-orange-300 transition-all duration-300">
            <CardContent className="p-6">
              <Textarea
                id="special_requirements"
                placeholder={t("placeholderText")}
                value={formData.special_requirements}
                onChange={(e) =>
                  updateFormData({ special_requirements: e.target.value })
                }
                className="min-h-[120px] text-lg border-none resize-none focus:ring-0 p-0"
              />
            </CardContent>
          </Card>
          <p className="text-sm text-gray-500 mt-3 text-center">
            💡 {t("helpText")}
          </p>
        </motion.div>
      </div>
    </motion.div>
  );
}
