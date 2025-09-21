import React from "react";
import { Badge } from "../ui/badge";
import {
  Building,
  Mountain,
  Utensils,
  TreePine,
  Waves,
  Sunrise,
  Moon,
  ShoppingBag,
  Camera,
  Palette,
  Music,
  Star,
  Sparkles,
} from "lucide-react";
import { motion } from "framer-motion";
import { useLanguage } from "../language/LanguageProvider";

export default function InterestsStep({ formData, updateFormData }) {
  const { t } = useLanguage();

  const allThemes = [
    { id: "heritage", icon: Building, emoji: "🏛️" },
    { id: "adventure", icon: Mountain, emoji: "🏔️" },
    { id: "food", icon: Utensils, emoji: "🍽️" },
    { id: "nature", icon: TreePine, emoji: "🌿" },
    { id: "beaches", icon: Waves, emoji: "🏖️" },
    { id: "spiritual", icon: Sunrise, emoji: "🕉️" },
    { id: "nightlife", icon: Moon, emoji: "🌙" },
    { id: "shopping", icon: ShoppingBag, emoji: "🛍️" },
    { id: "photography", icon: Camera, emoji: "📸" },
    { id: "art", icon: Palette, emoji: "🎨" },
    { id: "festivals", icon: Music, emoji: "🎵" },
    { id: "luxury", icon: Star, emoji: "✨" },
  ];

  // Destination-based theme mapping
  const getRelevantThemes = (destination) => {
    if (!destination) return allThemes;

    const dest = destination.toLowerCase();

    const coastalThemes = [
      "heritage",
      "food",
      "beaches",
      "spiritual",
      "nightlife",
      "shopping",
      "photography",
      "art",
      "festivals",
      "luxury",
    ];
    const mountainThemes = [
      "heritage",
      "adventure",
      "food",
      "nature",
      "spiritual",
      "photography",
      "art",
      "festivals",
      "luxury",
    ];
    const culturalThemes = [
      "heritage",
      "food",
      "spiritual",
      "nightlife",
      "shopping",
      "photography",
      "art",
      "festivals",
      "luxury",
    ];
    const metropolitanThemes = [
      "heritage",
      "food",
      "nightlife",
      "shopping",
      "photography",
      "art",
      "festivals",
      "luxury",
    ];
    const wildlifeThemes = [
      "adventure",
      "food",
      "nature",
      "photography",
      "festivals",
      "luxury",
    ];
    const desertThemes = [
      "heritage",
      "adventure",
      "food",
      "spiritual",
      "photography",
      "art",
      "festivals",
      "luxury",
    ];

    if (dest.includes("goa")) {
      return allThemes.filter((theme) => coastalThemes.includes(theme.id));
    } else if (
      dest.includes("himachal") ||
      dest.includes("shimla") ||
      dest.includes("manali") ||
      dest.includes("dharamshala")
    ) {
      return allThemes.filter((theme) => mountainThemes.includes(theme.id));
    } else if (
      dest.includes("kerala") ||
      dest.includes("kochi") ||
      dest.includes("alleppey") ||
      dest.includes("munnar")
    ) {
      return allThemes.filter((theme) =>
        [...coastalThemes, "nature"].includes(theme.id)
      );
    } else if (
      dest.includes("rajasthan") ||
      dest.includes("jaipur") ||
      dest.includes("udaipur") ||
      dest.includes("jodhpur")
    ) {
      return allThemes.filter((theme) => desertThemes.includes(theme.id));
    } else if (
      dest.includes("tamil nadu") ||
      dest.includes("chennai") ||
      dest.includes("pondicherry")
    ) {
      return allThemes.filter((theme) =>
        [...culturalThemes, "beaches"].includes(theme.id)
      );
    } else if (
      dest.includes("karnataka") ||
      dest.includes("bangalore") ||
      dest.includes("mysore") ||
      dest.includes("coorg")
    ) {
      return allThemes.filter((theme) =>
        [...culturalThemes, "nature"].includes(theme.id)
      );
    } else if (
      dest.includes("maharashtra") ||
      dest.includes("mumbai") ||
      dest.includes("pune")
    ) {
      return allThemes.filter((theme) => metropolitanThemes.includes(theme.id));
    } else if (
      dest.includes("west bengal") ||
      dest.includes("kolkata") ||
      dest.includes("darjeeling")
    ) {
      return allThemes.filter((theme) =>
        [...culturalThemes, "nature"].includes(theme.id)
      );
    } else if (
      dest.includes("assam") ||
      dest.includes("meghalaya") ||
      dest.includes("arunachal")
    ) {
      return allThemes.filter((theme) =>
        [...wildlifeThemes, "heritage", "spiritual"].includes(theme.id)
      );
    } else if (
      dest.includes("kashmir") ||
      dest.includes("ladakh") ||
      dest.includes("srinagar")
    ) {
      return allThemes.filter((theme) =>
        [...mountainThemes, "adventure"]
          .filter((t) => t !== "beaches")
          .includes(theme.id)
      );
    } else if (
      dest.includes("uttarakhand") ||
      dest.includes("dehradun") ||
      dest.includes("rishikesh")
    ) {
      return allThemes.filter((theme) =>
        [...mountainThemes, "spiritual"].includes(theme.id)
      );
    } else if (dest.includes("andaman") || dest.includes("lakshadweep")) {
      return allThemes.filter((theme) =>
        ["beaches", "adventure", "nature", "photography", "luxury"].includes(
          theme.id
        )
      );
    }

    return allThemes.filter((theme) =>
      [
        "heritage",
        "food",
        "nature",
        "spiritual",
        "shopping",
        "photography",
        "art",
        "festivals",
      ].includes(theme.id)
    );
  };

  const themes = getRelevantThemes(formData.destination);

  const toggleTheme = (themeId) => {
    const currentThemes = formData.themes || [];
    let updatedThemes;

    if (currentThemes.includes(themeId)) {
      updatedThemes = currentThemes.filter((id) => id !== themeId);
    } else {
      updatedThemes = [...currentThemes, themeId];
    }

    updateFormData({ themes: updatedThemes });
  };

  const selectedThemeCount = formData.themes?.length || 0;
  const isSelectionInvalid =
    selectedThemeCount > 0 &&
    (selectedThemeCount < 3 || selectedThemeCount > 5);

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5 }}
      className="space-y-8"
    >
      <div className="text-center mb-8">
        <h3 className="text-3xl font-bold text-gray-900 mb-3">
          {t("travelThemesInterest")}
        </h3>
        <p className="text-gray-600 text-lg">
          {formData.destination
            ? `${t("selectThemesExperience")} ${formData.destination}`
            : t("selectThemesExperience")}
        </p>
        {isSelectionInvalid && (
          <motion.p
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="text-red-500 text-sm mt-2"
          >
            {t("validation_select_themes", { selectedThemeCount })}
          </motion.p>
        )}
        {formData.destination && (
          <p className="text-sm text-blue-600 mt-2">
            💡 Themes are customized for {formData.destination}
          </p>
        )}
      </div>

      <div className="max-w-5xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
          {themes.map((theme, index) => {
            const isSelected = formData.themes?.includes(theme.id);
            const Icon = theme.icon;

            return (
              <motion.button
                key={theme.id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ delay: 0.3 + index * 0.05 }}
                onClick={() => toggleTheme(theme.id)}
                className={`p-5 rounded-2xl border-2 transition-all duration-300 text-center group hover:scale-105 ${
                  isSelected
                    ? "border-orange-500 bg-orange-50 shadow-lg scale-105"
                    : "border-gray-200 hover:border-gray-300 hover:shadow-md bg-white"
                }`}
              >
                <div className="flex flex-col items-center gap-3">
                  <div className="text-3xl mb-1">{theme.emoji}</div>
                  <div
                    className={`p-2 rounded-xl transition-all duration-300 ${
                      isSelected
                        ? "bg-orange-500 text-white"
                        : "bg-gray-100 text-gray-600 group-hover:bg-gray-200"
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                  </div>
                  <div className="text-center">
                    <span
                      className={`text-sm font-semibold leading-tight block ${
                        isSelected ? "text-orange-700" : "text-gray-700"
                      }`}
                    >
                      {t(`theme_${theme.id}`)}
                    </span>
                    <span className="text-xs text-gray-500 mt-1 block">
                      {t(`theme_${theme.id}_desc`)}
                    </span>
                  </div>
                </div>
              </motion.button>
            );
          })}
        </div>

        {formData.themes?.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.5 }}
            className="mt-8 text-center"
          >
            <div className="flex items-center justify-center gap-2 mb-4">
              <Sparkles className="w-5 h-5 text-orange-500" />
              <p className="text-lg font-semibold text-gray-700">
                {t("selectedThemes")}
              </p>
            </div>
            <div className="flex flex-wrap gap-3 justify-center max-w-2xl mx-auto">
              {formData.themes.map((themeId) => {
                const theme = themes.find((t) => t.id === themeId);
                return (
                  <Badge
                    key={themeId}
                    variant="secondary"
                    className="bg-gradient-to-r from-orange-100 to-red-100 text-orange-700 px-4 py-2 text-sm font-medium border border-orange-200"
                  >
                    {theme?.emoji} {t(`theme_${themeId}`)}
                  </Badge>
                );
              })}
            </div>
          </motion.div>
        )}
      </div>
    </motion.div>
  );
}
