import React, { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Input } from "../ui/input";
import { Label } from "../ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui/select";
import { Textarea } from "../ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "../ui/tabs";
import {
  Calendar,
  Clock,
  DollarSign,
  MapPin,
  Utensils,
  Home,
  Car,
  Plus,
  Minus,
  Save,
  X,
} from "lucide-react";
import { motion } from "framer-motion";

export default function CustomizationPanel({ option, trip, onSave, onCancel }) {
  const [customizedOption, setCustomizedOption] = useState({ ...option });
  const [selectedDay, setSelectedDay] = useState(1);

  const updateDayActivity = (dayIndex, activityIndex, updates) => {
    const updatedItineraries = [...customizedOption.daily_itineraries];
    const updatedActivities = [...updatedItineraries[dayIndex].activities];
    updatedActivities[activityIndex] = {
      ...updatedActivities[activityIndex],
      ...updates,
    };
    updatedItineraries[dayIndex] = {
      ...updatedItineraries[dayIndex],
      activities: updatedActivities,
    };

    // Recalculate costs
    const newTotalCost = calculateTotalCost(updatedItineraries);

    setCustomizedOption({
      ...customizedOption,
      daily_itineraries: updatedItineraries,
      total_estimated_cost: newTotalCost,
    });
  };

  const updateDayMeal = (dayIndex, mealIndex, updates) => {
    const updatedItineraries = [...customizedOption.daily_itineraries];
    const updatedMeals = [...updatedItineraries[dayIndex].meals];
    updatedMeals[mealIndex] = { ...updatedMeals[mealIndex], ...updates };
    updatedItineraries[dayIndex] = {
      ...updatedItineraries[dayIndex],
      meals: updatedMeals,
    };

    const newTotalCost = calculateTotalCost(updatedItineraries);

    setCustomizedOption({
      ...customizedOption,
      daily_itineraries: updatedItineraries,
      total_estimated_cost: newTotalCost,
    });
  };

  const addActivity = (dayIndex) => {
    const updatedItineraries = [...customizedOption.daily_itineraries];
    const newActivity = {
      time: "15:00",
      activity: "New Activity",
      location: `${trip.destination}`,
      duration: "2 hours",
      cost: 500,
      description: "Custom activity",
      category: "custom",
      coordinates: {
        lat: 0,
        lng: 0,
      },
    };

    updatedItineraries[dayIndex].activities.push(newActivity);
    const newTotalCost = calculateTotalCost(updatedItineraries);

    setCustomizedOption({
      ...customizedOption,
      daily_itineraries: updatedItineraries,
      total_estimated_cost: newTotalCost,
    });
  };

  const removeActivity = (dayIndex, activityIndex) => {
    const updatedItineraries = [...customizedOption.daily_itineraries];
    updatedItineraries[dayIndex].activities.splice(activityIndex, 1);
    const newTotalCost = calculateTotalCost(updatedItineraries);

    setCustomizedOption({
      ...customizedOption,
      daily_itineraries: updatedItineraries,
      total_estimated_cost: newTotalCost,
    });
  };

  const calculateTotalCost = (itineraries) => {
    return itineraries.reduce((sum, day) => {
      const dayTotal =
        (day.activities?.reduce((s, a) => s + (a.cost || 0), 0) || 0) +
        (day.meals?.reduce((s, m) => s + (m.cost || 0), 0) || 0) +
        (day.accommodation?.cost || 0) +
        (day.transportation?.reduce((s, t) => s + (t.cost || 0), 0) || 0);
      return sum + dayTotal;
    }, 0);
  };

  const selectedDayData = customizedOption.daily_itineraries?.[selectedDay - 1];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-slate-800">
            Customizing: {customizedOption.name}
          </h3>
          <p className="text-slate-600">
            Make adjustments to create your perfect itinerary
          </p>
        </div>
        <div className="text-right">
          <div className="text-sm text-slate-500">Total Cost</div>
          <div
            className={`text-xl font-bold ${
              customizedOption.total_estimated_cost > trip.total_budget
                ? "text-red-600"
                : "text-green-600"
            }`}
          >
            ₹{customizedOption.total_estimated_cost?.toLocaleString()}
          </div>
        </div>
      </div>

      <Tabs defaultValue="itinerary" className="w-full">
        <TabsList className="grid w-full grid-cols-3">
          <TabsTrigger value="itinerary">Daily Itinerary</TabsTrigger>
          <TabsTrigger value="accommodation">Accommodation</TabsTrigger>
          <TabsTrigger value="preferences">Preferences</TabsTrigger>
        </TabsList>

        <TabsContent value="itinerary" className="mt-6">
          <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
            {/* Day Selector */}
            <div className="lg:col-span-1">
              <h4 className="font-semibold text-slate-800 mb-3">Select Day</h4>
              <div className="space-y-2">
                {customizedOption.daily_itineraries?.map((day, index) => (
                  <Button
                    key={index}
                    variant={
                      selectedDay === day.day_number ? "default" : "outline"
                    }
                    onClick={() => setSelectedDay(day.day_number)}
                    className="w-full justify-start"
                  >
                    <Calendar className="w-4 h-4 mr-2" />
                    Day {day.day_number}
                  </Button>
                ))}
              </div>
            </div>

            {/* Day Details */}
            <div className="lg:col-span-3">
              {selectedDayData && (
                <div className="space-y-6">
                  {/* Activities */}
                  <Card>
                    <CardHeader>
                      <CardTitle className="flex items-center justify-between">
                        <span>Activities - Day {selectedDay}</span>
                        <Button
                          size="sm"
                          onClick={() => addActivity(selectedDay - 1)}
                          className="bg-green-600 hover:bg-green-700"
                        >
                          <Plus className="w-4 h-4 mr-1" />
                          Add Activity
                        </Button>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {selectedDayData.activities?.map(
                        (activity, activityIndex) => (
                          <motion.div
                            key={activityIndex}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            className="p-4 border border-slate-200 rounded-lg"
                          >
                            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                              <div>
                                <Label>Activity Name</Label>
                                <Input
                                  value={activity.activity}
                                  onChange={(e) =>
                                    updateDayActivity(
                                      selectedDay - 1,
                                      activityIndex,
                                      { activity: e.target.value }
                                    )
                                  }
                                />
                              </div>
                              <div>
                                <Label>Time</Label>
                                <Input
                                  type="time"
                                  value={activity.time}
                                  onChange={(e) =>
                                    updateDayActivity(
                                      selectedDay - 1,
                                      activityIndex,
                                      { time: e.target.value }
                                    )
                                  }
                                />
                              </div>
                              <div>
                                <Label>Cost (₹)</Label>
                                <div className="flex gap-2">
                                  <Input
                                    type="number"
                                    value={activity.cost}
                                    onChange={(e) =>
                                      updateDayActivity(
                                        selectedDay - 1,
                                        activityIndex,
                                        { cost: parseInt(e.target.value) || 0 }
                                      )
                                    }
                                  />
                                  <Button
                                    variant="outline"
                                    size="icon"
                                    onClick={() =>
                                      removeActivity(
                                        selectedDay - 1,
                                        activityIndex
                                      )
                                    }
                                    className="text-red-600 hover:text-red-700"
                                  >
                                    <Minus className="w-4 h-4" />
                                  </Button>
                                </div>
                              </div>
                              <div className="md:col-span-2">
                                <Label>Location</Label>
                                <Input
                                  value={activity.location}
                                  onChange={(e) =>
                                    updateDayActivity(
                                      selectedDay - 1,
                                      activityIndex,
                                      { location: e.target.value }
                                    )
                                  }
                                />
                              </div>
                              <div>
                                <Label>Duration</Label>
                                <Input
                                  value={activity.duration}
                                  onChange={(e) =>
                                    updateDayActivity(
                                      selectedDay - 1,
                                      activityIndex,
                                      { duration: e.target.value }
                                    )
                                  }
                                />
                              </div>
                              <div className="md:col-span-3">
                                <Label>Description</Label>
                                <Textarea
                                  value={activity.description}
                                  onChange={(e) =>
                                    updateDayActivity(
                                      selectedDay - 1,
                                      activityIndex,
                                      { description: e.target.value }
                                    )
                                  }
                                  rows={2}
                                />
                              </div>
                            </div>
                          </motion.div>
                        )
                      )}
                    </CardContent>
                  </Card>

                  {/* Meals */}
                  <Card>
                    <CardHeader>
                      <CardTitle>Meals - Day {selectedDay}</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      {selectedDayData.meals?.map((meal, mealIndex) => (
                        <div
                          key={mealIndex}
                          className="p-4 border border-slate-200 rounded-lg"
                        >
                          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                            <div>
                              <Label>Restaurant</Label>
                              <Input
                                value={meal.restaurant}
                                onChange={(e) =>
                                  updateDayMeal(selectedDay - 1, mealIndex, {
                                    restaurant: e.target.value,
                                  })
                                }
                              />
                            </div>
                            <div>
                              <Label>Cuisine Type</Label>
                              <Input
                                value={meal.cuisine}
                                onChange={(e) =>
                                  updateDayMeal(selectedDay - 1, mealIndex, {
                                    cuisine: e.target.value,
                                  })
                                }
                              />
                            </div>
                            <div>
                              <Label>Cost (₹)</Label>
                              <Input
                                type="number"
                                value={meal.cost}
                                onChange={(e) =>
                                  updateDayMeal(selectedDay - 1, mealIndex, {
                                    cost: parseInt(e.target.value) || 0,
                                  })
                                }
                              />
                            </div>
                            <div className="md:col-span-2">
                              <Label>Location</Label>
                              <Input
                                value={meal.location}
                                onChange={(e) =>
                                  updateDayMeal(selectedDay - 1, mealIndex, {
                                    location: e.target.value,
                                  })
                                }
                              />
                            </div>
                            <div>
                              <Label>Meal Type</Label>
                              <Badge variant="secondary" className="capitalize">
                                {meal.meal_type}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      ))}
                    </CardContent>
                  </Card>
                </div>
              )}
            </div>
          </div>
        </TabsContent>

        <TabsContent value="accommodation" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Accommodation Preferences</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label>Accommodation Type</Label>
                  <Select value={trip.accommodation_preference}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="budget">Budget</SelectItem>
                      <SelectItem value="mid-range">Mid-Range</SelectItem>
                      <SelectItem value="luxury">Luxury</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Transportation</Label>
                  <Select value={trip.transportation_preference}>
                    <SelectTrigger>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="public">Public Transport</SelectItem>
                      <SelectItem value="private">Private Transport</SelectItem>
                      <SelectItem value="mixed">Mixed</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="preferences" className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Trip Preferences</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div>
                  <Label>Special Requirements</Label>
                  <Textarea
                    value={trip.special_requirements || ""}
                    placeholder="Any special dietary requirements, accessibility needs, or other preferences..."
                    rows={3}
                  />
                </div>
                <div>
                  <Label>Budget Adjustment</Label>
                  <div className="flex items-center gap-4">
                    <span className="text-sm text-slate-600">
                      Original: ₹{trip.total_budget.toLocaleString()}
                    </span>
                    <span className="text-sm font-medium">
                      Current: ₹
                      {customizedOption.total_estimated_cost?.toLocaleString()}
                    </span>
                    <Badge
                      variant={
                        customizedOption.total_estimated_cost >
                        trip.total_budget
                          ? "destructive"
                          : "default"
                      }
                    >
                      {customizedOption.total_estimated_cost > trip.total_budget
                        ? "Over Budget"
                        : "Within Budget"}
                    </Badge>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Action Buttons */}
      <div className="flex justify-end gap-4 pt-6 border-t border-slate-200">
        <Button variant="outline" onClick={onCancel}>
          <X className="w-4 h-4 mr-2" />
          Cancel
        </Button>
        <Button
          onClick={() => onSave(customizedOption)}
          className="bg-green-600 hover:bg-green-700"
        >
          <Save className="w-4 h-4 mr-2" />
          Save Customization
        </Button>
      </div>
    </div>
  );
}
