import React, { useState, useEffect } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import {
  Globe,
  MessageCircle,
  Calendar,
  MapPin,
  Star,
  Mic,
  Volume2,
  Users,
  Heart,
  Sparkles,
  Navigation,
} from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const indianRegions = {
  north: {
    name: "North India",
    languages: ["hindi", "punjabi", "urdu"],
    states: [
      "Delhi",
      "Punjab",
      "Haryana",
      "Uttar Pradesh",
      "Uttarakhand",
      "Himachal Pradesh",
    ],
    avatar: "🏔️",
    colors: {
      primary: "from-orange-500 to-red-500",
      secondary: "from-orange-50 to-red-50",
      accent: "orange-600",
    },
    culturalTips: [
      "Namaste with joined palms is the traditional greeting",
      "Remove shoes when entering temples and homes",
      "Friday is considered auspicious for temple visits",
    ],
    localPhrases: {
      hindi: [
        {
          phrase: "Namaste",
          meaning: "Hello/Goodbye",
          pronunciation: "Na-mas-tay",
        },
        {
          phrase: "Dhanyawad",
          meaning: "Thank you",
          pronunciation: "Dhan-ya-waad",
        },
        {
          phrase: "Kitna paisa?",
          meaning: "How much?",
          pronunciation: "Kit-na pai-sa",
        },
      ],
    },
  },
  south: {
    name: "South India",
    languages: ["tamil", "telugu", "kannada", "malayalam"],
    states: [
      "Tamil Nadu",
      "Karnataka",
      "Andhra Pradesh",
      "Telangana",
      "Kerala",
    ],
    avatar: "🌴",
    colors: {
      primary: "from-green-500 to-teal-500",
      secondary: "from-green-50 to-teal-50",
      accent: "green-600",
    },
    culturalTips: [
      "Touch elders' feet as a sign of respect",
      "Banana leaves are used as plates in traditional meals",
      "Temple festivals are major cultural events",
    ],
    localPhrases: {
      tamil: [
        { phrase: "Vanakkam", meaning: "Hello", pronunciation: "Va-na-kam" },
        { phrase: "Nandri", meaning: "Thank you", pronunciation: "Nan-dri" },
        {
          phrase: "Evvalavu?",
          meaning: "How much?",
          pronunciation: "Ev-va-la-vu",
        },
      ],
    },
  },
  west: {
    name: "West India",
    languages: ["gujarati", "marathi", "hindi"],
    states: ["Maharashtra", "Gujarat", "Rajasthan", "Goa"],
    avatar: "🏖️",
    colors: {
      primary: "from-blue-500 to-purple-500",
      secondary: "from-blue-50 to-purple-50",
      accent: "blue-600",
    },
    culturalTips: [
      "Gujarati thali is served on silver plates traditionally",
      "Garba dance is integral to Gujarati culture",
      "Business hours may vary during festival seasons",
    ],
    localPhrases: {
      gujarati: [
        { phrase: "Namaste", meaning: "Hello", pronunciation: "Na-mas-tay" },
        { phrase: "Aabhar", meaning: "Thank you", pronunciation: "Aa-bhaar" },
        { phrase: "Ketlu?", meaning: "How much?", pronunciation: "Ket-lu" },
      ],
    },
  },
  east: {
    name: "East India",
    languages: ["bengali", "odia", "hindi"],
    states: ["West Bengal", "Odisha", "Bihar", "Jharkhand"],
    avatar: "🎭",
    colors: {
      primary: "from-yellow-500 to-amber-500",
      secondary: "from-yellow-50 to-amber-50",
      accent: "yellow-600",
    },
    culturalTips: [
      "Fish is a staple in Bengali cuisine",
      "Durga Puja is the biggest festival in Bengal",
      "Intellectual discussions are highly valued",
    ],
    localPhrases: {
      bengali: [
        { phrase: "Namaskar", meaning: "Hello", pronunciation: "Na-mas-kar" },
        {
          phrase: "Dhonnobad",
          meaning: "Thank you",
          pronunciation: "Dhon-no-bad",
        },
        {
          phrase: "Koto taka?",
          meaning: "How much?",
          pronunciation: "Ko-to ta-ka",
        },
      ],
    },
  },
};

const languages = {
  english: { name: "English", native: "English", flag: "🇬🇧" },
  hindi: { name: "Hindi", native: "हिंदी", flag: "🇮🇳" },
  tamil: { name: "Tamil", native: "தமிழ்", flag: "🇮🇳" },
  bengali: { name: "Bengali", native: "বাংলা", flag: "🇮🇳" },
  gujarati: { name: "Gujarati", native: "ગુજરાતી", flag: "🇮🇳" },
  marathi: { name: "Marathi", native: "मराठी", flag: "🇮🇳" },
  telugu: { name: "Telugu", native: "తెలుగు", flag: "🇮🇳" },
  kannada: { name: "Kannada", native: "ಕನ್ನಡ", flag: "🇮🇳" },
  malayalam: { name: "Malayalam", native: "മലയാളം", flag: "🇮🇳" },
  punjabi: { name: "Punjabi", native: "ਪੰਜਾਬੀ", flag: "🇮🇳" },
};

export default function RegionalAssistant({ trip, onUpdateTrip }) {
  const [selectedRegion, setSelectedRegion] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState("english");
  const [isListening, setIsListening] = useState(false);
  const [currentTip, setCurrentTip] = useState(0);
  const [showPhrases, setShowPhrases] = useState(false);

  useEffect(() => {
    // Auto-detect region based on destination
    if (trip?.destination) {
      const destination = trip.destination.toLowerCase();
      for (const [regionKey, regionData] of Object.entries(indianRegions)) {
        if (
          regionData.states.some((state) =>
            destination.includes(state.toLowerCase())
          )
        ) {
          setSelectedRegion(regionKey);
          break;
        }
      }
    }
  }, [trip]);

  const handleLanguageChange = (language) => {
    setSelectedLanguage(language);
    if (onUpdateTrip) {
      onUpdateTrip({ ...trip, preferred_language: language });
    }
  };

  const handleVoiceAssistant = () => {
    setIsListening(!isListening);
    // Mock voice recognition
    setTimeout(() => setIsListening(false), 3000);
  };

  const region = selectedRegion ? indianRegions[selectedRegion] : null;

  if (!region) {
    return (
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-blue-600" />
            <span>Regional Travel Assistant</span>
          </CardTitle>
        </CardHeader>
        <CardContent className="p-6 text-center">
          <div className="text-slate-500">
            <MapPin className="w-12 h-12 mx-auto mb-4 opacity-50" />
            <p>Select a destination to activate regional assistance</p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Regional Header */}
      <Card
        className={`border-0 shadow-lg bg-gradient-to-r ${region.colors.secondary}`}
      >
        <CardHeader className="text-center pb-4">
          <div className="text-6xl mb-4">{region.avatar}</div>
          <CardTitle className="text-2xl font-bold text-slate-800">
            Welcome to {region.name}
          </CardTitle>
          <p className="text-slate-600">Your AI-powered regional companion</p>
        </CardHeader>
      </Card>

      {/* Language Selector */}
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Globe className="w-5 h-5 text-blue-600" />
            Choose Your Language
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-3 gap-3 mb-4">
            {region.languages.concat(["english"]).map((lang) => {
              const langData = languages[lang];
              return (
                <Button
                  key={lang}
                  variant={selectedLanguage === lang ? "default" : "outline"}
                  onClick={() => handleLanguageChange(lang)}
                  className={`h-auto p-4 flex flex-col items-center gap-2 ${
                    selectedLanguage === lang
                      ? `bg-gradient-to-r ${region.colors.primary} hover:opacity-90`
                      : "hover:bg-slate-50"
                  }`}
                >
                  <span className="text-2xl">{langData.flag}</span>
                  <div className="text-center">
                    <div className="font-semibold text-sm">
                      {langData.native}
                    </div>
                    <div className="text-xs opacity-75">{langData.name}</div>
                  </div>
                </Button>
              );
            })}
          </div>

          {/* Voice Assistant */}
          <Button
            onClick={handleVoiceAssistant}
            className={`w-full ${
              isListening
                ? "bg-red-500 hover:bg-red-600 animate-pulse"
                : `bg-gradient-to-r ${region.colors.primary} hover:opacity-90`
            }`}
            disabled={isListening}
          >
            <Mic className="w-5 h-5 mr-2" />
            {isListening
              ? "Listening..."
              : `Voice Assistant in ${languages[selectedLanguage].native}`}
          </Button>
        </CardContent>
      </Card>

      {/* Cultural Tips */}
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Heart className="w-5 h-5 text-red-600" />
              Cultural Insights
            </div>
            <Badge
              variant="secondary"
              className={`bg-${region.colors.accent}/10 text-${region.colors.accent}`}
            >
              Local Tips
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <AnimatePresence mode="wait">
            <motion.div
              key={currentTip}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              className="text-center p-4 bg-slate-50 rounded-lg border border-slate-200"
            >
              <div className="text-lg text-slate-800 mb-3">
                💡 {region.culturalTips[currentTip]}
              </div>
              <div className="flex justify-center gap-2">
                {region.culturalTips.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentTip(index)}
                    className={`w-2 h-2 rounded-full transition-all ${
                      currentTip === index
                        ? `bg-${region.colors.accent}`
                        : "bg-slate-300"
                    }`}
                  />
                ))}
              </div>
            </motion.div>
          </AnimatePresence>
        </CardContent>
      </Card>

      {/* Local Phrases */}
      <Card className="border-slate-200 shadow-sm bg-white">
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <MessageCircle className="w-5 h-5 text-green-600" />
              Essential Phrases
            </div>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setShowPhrases(!showPhrases)}
            >
              {showPhrases ? "Hide" : "Show"} Phrases
            </Button>
          </CardTitle>
        </CardHeader>
        <AnimatePresence>
          {showPhrases && (
            <motion.div
              initial={{ opacity: 0, height: 0 }}
              animate={{ opacity: 1, height: "auto" }}
              exit={{ opacity: 0, height: 0 }}
            >
              <CardContent>
                {Object.entries(region.localPhrases).map(
                  ([language, phrases]) => (
                    <div key={language} className="mb-4">
                      <h4 className="font-semibold text-slate-700 mb-3 flex items-center gap-2">
                        <span className="text-xl">
                          {languages[language]?.flag}
                        </span>
                        {languages[language]?.native}
                      </h4>
                      <div className="space-y-2">
                        {phrases.map((phrase, index) => (
                          <div
                            key={index}
                            className="p-3 bg-slate-50 rounded-lg border border-slate-200"
                          >
                            <div className="flex items-center justify-between">
                              <div>
                                <div className="font-medium text-slate-800">
                                  {phrase.phrase}
                                </div>
                                <div className="text-sm text-slate-600">
                                  {phrase.meaning} •{" "}
                                  <em>{phrase.pronunciation}</em>
                                </div>
                              </div>
                              <Button
                                variant="ghost"
                                size="icon"
                                className="text-slate-500"
                              >
                                <Volume2 className="w-4 h-4" />
                              </Button>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )
                )}
              </CardContent>
            </motion.div>
          )}
        </AnimatePresence>
      </Card>

      {/* Quick Actions */}
      <div className="grid grid-cols-2 gap-4">
        <Button
          variant="outline"
          className="h-auto p-4 flex flex-col items-center gap-2 hover:bg-slate-50"
        >
          <Calendar className="w-6 h-6 text-purple-600" />
          <span className="font-medium">Local Festivals</span>
          <span className="text-xs text-slate-500">Upcoming events</span>
        </Button>
        <Button
          variant="outline"
          className="h-auto p-4 flex flex-col items-center gap-2 hover:bg-slate-50"
        >
          <Users className="w-6 h-6 text-blue-600" />
          <span className="font-medium">Local Guides</span>
          <span className="text-xs text-slate-500">Connect with experts</span>
        </Button>
      </div>
    </div>
  );
}
