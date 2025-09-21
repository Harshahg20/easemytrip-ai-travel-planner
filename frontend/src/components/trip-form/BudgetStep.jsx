import React from "react";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { DollarSign, TrendingUp, PiggyBank } from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "../language/LanguageProvider";

const currencies = [
  { code: "INR", symbol: "₹", name: "Indian Rupee" },
  { code: "USD", symbol: "$", name: "US Dollar" },
  { code: "EUR", symbol: "€", name: "Euro" },
  { code: "GBP", symbol: "£", name: "British Pound" },
];

export default function BudgetStep({ formData, updateFormData }) {
  const { t } = useLanguage();
  const selectedCurrency =
    currencies.find((c) => c.code === formData.currency) || currencies[0];

  const budgetRanges = [
    {
      label: t("budgetExplorer"),
      range: "₹2,000-5,000/day",
      color: "bg-emerald-50 text-emerald-700 border-emerald-200",
      icon: "💰",
      description: t("budgetDesc1"),
    },
    {
      label: t("comfortTraveler"),
      range: "₹5,000-12,000/day",
      color: "bg-blue-50 text-blue-700 border-blue-200",
      icon: "🏨",
      description: t("budgetDesc2"),
    },
    {
      label: t("luxuryExperience"),
      range: "₹12,000+/day",
      color: "bg-purple-50 text-purple-700 border-purple-200",
      icon: "✨",
      description: t("budgetDesc3"),
    },
  ];

  return (
    <motion.div
      className="space-y-8"
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
    >
      <div className="text-center mb-8">
        <h3 className="text-3xl font-bold text-slate-800 mb-3">
          {t("whatsYourBudget")}
        </h3>
        <p className="text-slate-600 text-lg">{t("includeAllExpenses")}</p>
      </div>

      <div className="max-w-lg mx-auto space-y-6">
        <div className="flex gap-4">
          <div className="flex-1">
            <Label
              htmlFor="budget"
              className="text-base font-semibold text-slate-700 mb-3 flex items-center gap-2"
            >
              <PiggyBank
                className="w-5 h-5 text-emerald-600"
                aria-hidden="true"
              />
              {t("totalBudget")}
            </Label>
            <div className="relative">
              <span
                className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-500 text-lg font-semibold"
                aria-hidden="true"
              >
                {selectedCurrency.symbol}
              </span>
              <Input
                id="budget"
                type="number"
                min="0"
                step="1000"
                placeholder="50000"
                value={formData.total_budget}
                onChange={(e) =>
                  updateFormData({ total_budget: e.target.value })
                }
                className="pl-10 h-12 text-lg border-slate-300 rounded-xl focus:border-amber-400 focus:ring-2 focus:ring-amber-200 transition-all duration-200"
                aria-describedby="budget-help"
              />
            </div>
            <p id="budget-help" className="text-sm text-slate-500 mt-2">
              {t("budgetHelp")} {selectedCurrency.name}
            </p>
          </div>
          <div>
            <Label className="text-base font-semibold text-slate-700 mb-3 block">
              {t("currency")}
            </Label>
            <Select
              value={formData.currency}
              onValueChange={(value) => updateFormData({ currency: value })}
            >
              <SelectTrigger className="w-24 h-12 text-base border-slate-300 rounded-xl focus:border-amber-400 focus:ring-2 focus:ring-amber-200">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {currencies.map((currency) => (
                  <SelectItem key={currency.code} value={currency.code}>
                    {currency.code}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        {/* Budget Guidelines for India */}
        <div className="bg-slate-50 rounded-xl p-6 border border-slate-200">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-amber-600" aria-hidden="true" />
            <h4 className="font-bold text-slate-800 text-lg">
              {t("budgetGuide")}
            </h4>
          </div>
          <div className="space-y-3">
            {budgetRanges.map((range, index) => (
              <div
                key={index}
                className={`flex flex-col p-4 rounded-lg border ${range.color} transition-all duration-200`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    <span
                      className="text-2xl"
                      role="img"
                      aria-label={range.label}
                    >
                      {range.icon}
                    </span>
                    <span className="font-semibold">{range.label}</span>
                  </div>
                  <span className="font-bold text-sm">{range.range}</span>
                </div>
                <p className="text-xs opacity-80">{range.description}</p>
              </div>
            ))}
          </div>
          <div className="mt-4 p-3 bg-amber-50 rounded-lg border border-amber-200">
            <p className="text-sm text-amber-700 font-medium text-center">
              💡 {t("disclaimer")}
            </p>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
