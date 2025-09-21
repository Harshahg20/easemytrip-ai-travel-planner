import React from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import {
  CloudSun,
  Clock,
  Sparkles,
  ArrowRight,
  AlertCircle,
} from "lucide-react";
import { motion } from "framer-motion";

const updates = [
  {
    id: 1,
    type: "weather",
    title: "Weather Update: Afternoon Showers Expected",
    description:
      "Light rain is forecast for this afternoon. We suggest moving the outdoor market visit to tomorrow and exploring the City Museum instead.",
    action: "Adjust Itinerary",
    icon: CloudSun,
    color: "blue",
  },
  {
    id: 2,
    type: "delay",
    title: "Traffic Alert: Heavy Congestion on Main St.",
    description:
      "There's a significant traffic delay near your next activity. We recommend leaving 20 minutes earlier or taking the metro.",
    action: "View Alternative Route",
    icon: Clock,
    color: "amber",
  },
  {
    id: 3,
    type: "opportunity",
    title: "New Opportunity: Local Music Festival Tonight",
    description:
      "A popular local music festival is happening near your hotel tonight. Would you like to add it to your evening plans?",
    action: "Add to Itinerary",
    icon: Sparkles,
    color: "emerald",
  },
  {
    id: 4,
    type: "alert",
    title: "Attraction Alert: Heritage Palace Closed",
    description:
      "The Heritage Palace is unexpectedly closed for a private event today. We have found an alternative, the historic Governor's House, nearby.",
    action: "View Alternative",
    icon: AlertCircle,
    color: "red",
  },
];

const getIconColor = (color) => {
  switch (color) {
    case "blue":
      return "text-blue-600";
    case "amber":
      return "text-amber-600";
    case "emerald":
      return "text-emerald-600";
    case "red":
      return "text-red-600";
    default:
      return "text-slate-600";
  }
};

const getBgColor = (color) => {
  switch (color) {
    case "blue":
      return "bg-blue-50 border-blue-200";
    case "amber":
      return "bg-amber-50 border-amber-200";
    case "emerald":
      return "bg-emerald-50 border-emerald-200";
    case "red":
      return "bg-red-50 border-red-200";
    default:
      return "bg-slate-50 border-slate-200";
  }
};

export default function RealTimeUpdates({ trip }) {
  return (
    <Card className="border-slate-200 shadow-sm bg-white">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-amber-500" />
          Smart Adjustments
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <p className="text-sm text-slate-600 mb-6">
          Your trip is alive! We monitor conditions in real-time to suggest
          smart adjustments, ensuring you have the best possible experience.
        </p>
        <div className="space-y-4">
          {updates.map((update, index) => {
            const Icon = update.icon;
            return (
              <motion.div
                key={update.id}
                initial={{ opacity: 0, x: -20 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.5, delay: index * 0.1 }}
              >
                <Card className={`${getBgColor(update.color)}`}>
                  <CardContent className="p-4 flex items-start gap-4">
                    <div
                      className={`mt-1 flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${getIconColor(
                        update.color
                      )} bg-white`}
                    >
                      <Icon className="w-5 h-5" />
                    </div>
                    <div className="flex-1">
                      <h4 className="font-semibold text-slate-800 mb-1">
                        {update.title}
                      </h4>
                      <p className="text-sm text-slate-600 mb-3">
                        {update.description}
                      </p>
                      <Button
                        variant="link"
                        className="p-0 h-auto text-blue-600 font-semibold"
                      >
                        {update.action}
                        <ArrowRight className="w-4 h-4 ml-1" />
                      </Button>
                    </div>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
