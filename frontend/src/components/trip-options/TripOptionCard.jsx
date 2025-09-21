import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Check, Settings, DollarSign } from "lucide-react";
import { useLanguage } from "../language/LanguageProvider";

export default function TripOptionCard({
  option,
  trip,
  icon: Icon,
  onSelect,
  onCustomize,
}) {
  const { t } = useLanguage();

  return (
    <Card className="h-full flex flex-col bg-white shadow-lg hover:shadow-xl transition-shadow duration-300 border-2 border-transparent hover:border-amber-400">
      <CardHeader className="flex flex-row items-center gap-4 pb-4">
        <div className="w-12 h-12 bg-gradient-to-br from-amber-400 to-orange-500 text-white rounded-lg flex items-center justify-center">
          <Icon className="w-6 h-6" />
        </div>
        <div>
          <CardTitle className="text-xl font-bold text-slate-800">
            {t(`option_${option.id}_name`)}
          </CardTitle>
          <Badge
            variant="secondary"
            className="mt-1 bg-slate-100 text-slate-600"
          >
            {option.focus}
          </Badge>
        </div>
      </CardHeader>
      <CardContent className="flex flex-col flex-grow">
        <p className="text-slate-600 mb-4 text-sm min-h-[60px]">
          {t(`option_${option.id}_desc`)}
        </p>

        <div className="flex justify-between items-center mb-6 p-3 bg-slate-50 rounded-lg">
          <span className="text-sm font-medium text-slate-600">
            Estimated Cost:
          </span>
          <span className="text-lg font-bold text-slate-800 flex items-center">
            <DollarSign className="w-4 h-4 mr-1 text-emerald-600" />
            {option.total_estimated_cost.toLocaleString()}
          </span>
        </div>

        <div className="flex-grow"></div>

        <div className="flex flex-col gap-3 mt-auto">
          <Button
            onClick={onSelect}
            className="w-full bg-slate-800 hover:bg-slate-900 text-white"
          >
            <Check className="w-4 h-4 mr-2" />
            {t("chooseThisPlan")}
          </Button>
          <Button
            onClick={onCustomize}
            variant="outline"
            className="w-full border-slate-300 hover:bg-slate-100"
          >
            <Settings className="w-4 h-4 mr-2" />
            {t("customizeThisPlan")}
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
