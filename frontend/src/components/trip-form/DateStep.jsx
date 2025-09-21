import React from "react";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import { Calendar, Clock, Sunrise } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "../language/LanguageProvider";

export default function DatesStep({ formData, updateFormData }) {
  const { t } = useLanguage();
  const today = new Date().toISOString().split("T")[0];

  const calculateDays = () => {
    if (formData.start_date && formData.end_date) {
      const start = new Date(formData.start_date);
      const end = new Date(formData.end_date);
      if (end < start) return 0;
      return Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
    }
    return 0;
  };

  const days = calculateDays();

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <div className="text-center mb-8">
        <h3 className="text-3xl font-bold text-slate-800 mb-3">
          {t("whenTraveling")}
        </h3>
        <p className="text-slate-600 text-lg">{t("selectTravelDates")}</p>
      </div>

      <div className="max-w-lg mx-auto">
        <div className="grid grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.3 }}
          >
            <Label
              htmlFor="start_date"
              className="text-lg font-semibold text-slate-700 mb-3 block flex items-center gap-2"
            >
              <Sunrise className="w-4 h-4 text-slate-500" />
              {t("startDate")}
            </Label>
            <Input
              id="start_date"
              type="date"
              min={today}
              value={formData.start_date}
              onChange={(e) => updateFormData({ start_date: e.target.value })}
              className="h-14 text-lg border-2 border-slate-200 rounded-xl focus:border-slate-400 focus:ring-4 focus:ring-slate-100 transition-all duration-300"
            />
          </motion.div>
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ delay: 0.4 }}
          >
            <Label
              htmlFor="end_date"
              className="text-lg font-semibold text-slate-700 mb-3 block flex items-center gap-2"
            >
              <Calendar className="w-4 h-4 text-slate-500" />
              {t("endDate")}
            </Label>
            <Input
              id="end_date"
              type="date"
              min={formData.start_date || today}
              value={formData.end_date}
              onChange={(e) => updateFormData({ end_date: e.target.value })}
              className="h-14 text-lg border-2 border-slate-200 rounded-xl focus:border-slate-400 focus:ring-4 focus:ring-slate-100 transition-all duration-300"
            />
          </motion.div>
        </div>

        {days > 0 && (
          <motion.div
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-8 text-center"
          >
            <div className="inline-flex items-center gap-3 px-6 py-4 bg-gradient-to-r from-slate-50 to-blue-50 text-slate-700 rounded-2xl border-2 border-slate-200 shadow-sm">
              <Clock className="w-5 h-5" />
              <span className="text-xl font-bold">
                {days} {t("days")}
              </span>
              <span className="text-lg">{t("adventures")}</span>
            </div>
          </motion.div>
        )}

        {/* Travel tips */}
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: 0.6 }}
          className="mt-8 p-4 bg-blue-50 rounded-xl border border-blue-200"
        >
          <h4 className="font-semibold text-blue-800 mb-2">
            💡 {t("travelTips")}
          </h4>
          <ul className="text-sm text-blue-700 space-y-1">
            <li>• {t("tip1")}</li>
            <li>• {t("tip2")}</li>
            <li>• {t("tip3")}</li>
          </ul>
        </motion.div>
      </div>
    </motion.div>
  );
}
