import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { createPageUrl } from "../utils";
import { useLanguage } from "../components/language/LanguageProvider";
import { Button } from "../components/ui/button";
import { Input } from "../components/ui/input";
import { Search, Sparkles } from "lucide-react";

export default function Landing() {
  const [destination, setDestination] = useState("");
  const navigate = useNavigate();
  const { t } = useLanguage();

  const handleSearch = () => {
    if (destination.trim()) {
      navigate(
        `${createPageUrl("TripForm")}?destination=${encodeURIComponent(
          destination
        )}`
      );
    } else {
      navigate(createPageUrl("TripForm"));
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  return (
    <div className="min-h-screen bg-white">
      {/* Simplified Hero Section */}
      <section className="relative flex items-center justify-center min-h-screen overflow-hidden bg-gradient-to-br from-amber-50 via-white to-orange-50">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-slate-900 mb-6 leading-tight">
            {t("heroTitle")}
            <span className="block text-amber-600 mt-2">
              {t("heroSubtitle")}
            </span>
          </h1>

          <p className="text-xl lg:text-2xl text-slate-600 mb-12 max-w-3xl mx-auto leading-relaxed">
            {t("heroDescription")}
          </p>

          {/* Search Bar */}
          <div className="max-w-2xl mx-auto mb-8">
            <div className="flex gap-3 bg-white rounded-2xl p-3 shadow-lg border border-slate-200">
              <div className="flex-1 relative">
                <label htmlFor="destination-search" className="sr-only">
                  {t("searchPlaceholder")}
                </label>
                <Search
                  className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400"
                  aria-hidden="true"
                />
                <Input
                  id="destination-search"
                  placeholder={t("searchPlaceholder")}
                  value={destination}
                  onChange={(e) => setDestination(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="pl-12 bg-transparent border-none text-slate-900 placeholder-slate-500 h-12 text-lg rounded-xl focus:ring-2 focus:ring-amber-400"
                />
              </div>
              <Button
                onClick={handleSearch}
                size="lg"
                className="bg-amber-500 hover:bg-amber-600 text-white rounded-xl px-8 h-12 text-lg font-semibold shadow-sm hover:shadow-md transition-all duration-200 focus:ring-2 focus:ring-amber-500 focus:ring-offset-2"
                aria-label={t("planMyTrip")}
              >
                <Sparkles className="w-5 h-5 mr-2" aria-hidden="true" />
                {t("planMyTrip")}
              </Button>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}
