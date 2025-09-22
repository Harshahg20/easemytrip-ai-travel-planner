import React from "react";
import { Link, useLocation } from "react-router-dom";
import { createPageUrl } from "./utils";
import {
  LanguageProvider,
  useLanguage,
} from "./components/language/LanguageProvider";
import { MapPin, Calendar, DollarSign, User, Menu, Globe } from "lucide-react";
import { Sheet, SheetContent, SheetTrigger } from "./components/ui/sheet";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "./components/ui/dropdown-menu";
import { Button } from "./components/ui/button";

function LayoutContent({ children, currentPageName }) {
  const location = useLocation();
  const [isOpen, setIsOpen] = React.useState(false);
  const { currentLanguage, changeLanguage, t } = useLanguage();

  const navigationItems = [
    {
      title: t("home"),
      url: createPageUrl("Landing"),
      icon: MapPin,
    },
    {
      title: t("planTrip"),
      url: createPageUrl("TripForm"),
      icon: Calendar,
    },
    {
      title: t("myTrips"),
      url: createPageUrl("MyTrips"),
      icon: DollarSign,
    },
  ];

  const languages = [
    { code: "english", name: "English", native: "English", flag: "🇬🇧" },
    { code: "hindi", name: "Hindi", native: "हिंदी", flag: "🇮🇳" },
    { code: "tamil", name: "Tamil", native: "தமிழ்", flag: "🇮🇳" },
    { code: "kannada", name: "Kannada", native: "ಕನ್ನಡ", flag: "🇮🇳" },
    { code: "malayalam", name: "Malayalam", native: "മലയാളം", flag: "🇮🇳" },
    { code: "telugu", name: "Telugu", native: "తెలుగు", flag: "🇮🇳" },
  ];

  const currentLangInfo = languages.find(
    (lang) => lang.code === currentLanguage
  );

  const NavItems = () => (
    <>
      {navigationItems.map((item) => (
        <Link
          key={item.title}
          to={item.url}
          className={`flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 text-sm font-medium focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 ${
            location.pathname === item.url
              ? "bg-amber-50 text-amber-800 shadow-sm border border-amber-200"
              : "text-slate-700 hover:bg-slate-50 hover:text-slate-900"
          }`}
          onClick={() => setIsOpen(false)}
          aria-current={location.pathname === item.url ? "page" : undefined}
        >
          <item.icon className="w-5 h-5" aria-hidden="true" />
          {item.title}
        </Link>
      ))}
    </>
  );

  return (
    <div className="min-h-screen bg-slate-50">
      <style>
        {`
          :root {
            --yatra-primary: #f59e0b;
            --yatra-secondary: #d97706;
            --yatra-accent: #fbbf24;
            --yatra-warm: #fef3c7;
            --yatra-text: #1e293b;
            --yatra-text-light: #64748b;
            --yatra-border: #e2e8f0;
          }
          
          .focus-visible:focus {
            outline: 2px solid #f59e0b;
            outline-offset: 2px;
          }
          
          .text-warm {
            color: #92400e;
          }
          
          .shadow-warm {
            box-shadow: 0 1px 3px 0 rgba(245, 158, 11, 0.1), 0 1px 2px 0 rgba(245, 158, 11, 0.06);
          }
        `}
      </style>

      {/* Navigation Header */}
      <header className="sticky top-0 z-50 bg-white/95 backdrop-blur-sm border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            {/* Logo */}
            <Link
              to={createPageUrl("Landing")}
              className="flex items-center gap-3 hover:opacity-80 transition-opacity focus:outline-none focus:ring-2 focus:ring-amber-500 focus:ring-offset-2 rounded-lg p-1"
              aria-label="Tripora - AI Travel Planner"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-amber-500 rounded-xl flex items-center justify-center shadow-warm">
                <MapPin className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div className="flex flex-col">
                <span className="text-xl font-bold text-slate-800">
                  {t("tripora")}
                </span>
                <span className="text-xs text-slate-500 -mt-1">
                  {t("aiTravelPlanner")}
                </span>
              </div>
            </Link>

            {/* Desktop Navigation */}
            <nav
              className="hidden md:flex items-center gap-1"
              role="navigation"
              aria-label="Main navigation"
            >
              <NavItems />
            </nav>

            {/* Language Selector & User Profile */}
            <div className="hidden md:flex items-center gap-3">
              {/* Language Dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button
                    variant="ghost"
                    className="flex items-center gap-2 px-3 py-2 text-sm font-medium text-slate-700 hover:bg-slate-100 hover:text-slate-900 rounded-lg focus:ring-2 focus:ring-amber-500"
                  >
                    <Globe className="w-4 h-4" />
                    <span className="text-lg">{currentLangInfo?.flag}</span>
                    <span className="hidden sm:inline">
                      {currentLangInfo?.native}
                    </span>
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  {languages.map((language) => (
                    <DropdownMenuItem
                      key={language.code}
                      onClick={() => changeLanguage(language.code)}
                      className={`flex items-center gap-3 ${
                        currentLanguage === language.code
                          ? "bg-amber-50 text-amber-800"
                          : ""
                      }`}
                    >
                      <span className="text-lg">{language.flag}</span>
                      <div className="flex flex-col">
                        <span className="font-medium">{language.native}</span>
                        <span className="text-xs text-slate-500">
                          {language.name}
                        </span>
                      </div>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              <Button
                variant="ghost"
                size="icon"
                className="w-9 h-9 rounded-full bg-amber-100 hover:bg-amber-200 text-amber-700 focus:ring-2 focus:ring-amber-500"
                aria-label="User profile"
              >
                <User className="w-4 h-4" aria-hidden="true" />
              </Button>
            </div>

            {/* Mobile Menu */}
            <Sheet open={isOpen} onOpenChange={setIsOpen}>
              <SheetTrigger asChild>
                <Button
                  variant="ghost"
                  size="icon"
                  className="md:hidden focus:ring-2 focus:ring-amber-500"
                  aria-label="Open navigation menu"
                >
                  <Menu className="h-5 w-5" aria-hidden="true" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-80 bg-white">
                <div className="flex flex-col gap-6 pt-6">
                  <div className="flex items-center gap-3 px-4 pb-4 border-b border-slate-200">
                    <div className="w-10 h-10 bg-gradient-to-br from-amber-400 to-amber-500 rounded-xl flex items-center justify-center">
                      <MapPin
                        className="w-6 h-6 text-white"
                        aria-hidden="true"
                      />
                    </div>
                    <div>
                      <span className="text-lg font-bold text-slate-800">
                        {t("tripora")}
                      </span>
                      <p className="text-sm text-slate-500">
                        {t("aiTravelPlanner")}
                      </p>
                    </div>
                  </div>

                  {/* Mobile Language Selector */}
                  <div className="px-4">
                    <h3 className="text-sm font-semibold text-slate-800 mb-3 flex items-center gap-2">
                      <Globe className="w-4 h-4" />
                      {t("chooseLanguage")}
                    </h3>
                    <div className="grid grid-cols-2 gap-2">
                      {languages.map((language) => (
                        <button
                          key={language.code}
                          onClick={() => {
                            changeLanguage(language.code);
                            setIsOpen(false);
                          }}
                          className={`flex items-center gap-2 p-3 rounded-lg border-2 transition-all ${
                            currentLanguage === language.code
                              ? "border-amber-500 bg-amber-50 text-amber-800"
                              : "border-slate-200 hover:border-slate-300 bg-white"
                          }`}
                        >
                          <span className="text-lg">{language.flag}</span>
                          <div className="text-left">
                            <div className="font-medium text-xs">
                              {language.native}
                            </div>
                            <div className="text-xs text-slate-500">
                              {language.name}
                            </div>
                          </div>
                        </button>
                      ))}
                    </div>
                  </div>

                  <nav
                    className="flex flex-col gap-2 px-4"
                    role="navigation"
                    aria-label="Mobile navigation"
                  >
                    <NavItems />
                  </nav>
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1" id="main-content" role="main">
        {children}
      </main>

      {/* Footer */}
      <footer className="bg-slate-800 text-slate-100" role="contentinfo">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="text-center text-sm text-slate-400">
            <p>&copy; 2025 {t("tripora")}. All rights reserved.</p>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default function Layout({ children, currentPageName }) {
  return (
    <LanguageProvider>
      <LayoutContent children={children} currentPageName={currentPageName} />
    </LanguageProvider>
  );
}
