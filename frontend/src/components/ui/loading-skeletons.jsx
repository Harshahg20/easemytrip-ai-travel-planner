import { Skeleton } from "./skeleton";
import { Loader2 } from "lucide-react";

// Day Selector Skeleton
export function DaySelectorSkeleton({ count = 3 }) {
  return (
    <div className="flex gap-3 overflow-x-auto pb-2">
      {Array.from({ length: count }, (_, index) => (
        <div
          key={index}
          className="min-w-[140px] h-auto p-4 flex flex-col items-start gap-2 rounded-lg border border-slate-200 bg-white"
        >
          <div className="flex items-center gap-2">
            <Skeleton className="h-4 w-12" />
            <Loader2 className="w-3 h-3 animate-spin text-slate-400" />
          </div>
          <Skeleton className="h-3 w-16" />
          <Skeleton className="h-5 w-20" />
        </div>
      ))}
    </div>
  );
}

// Activity Item Skeleton
export function ActivityItemSkeleton() {
  return (
    <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-slate-200">
      <Skeleton className="w-12 h-12 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="flex items-center justify-between">
          <Skeleton className="h-4 w-32" />
          <Skeleton className="h-4 w-16" />
        </div>
        <Skeleton className="h-3 w-24" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-3/4" />
      </div>
    </div>
  );
}

// Meal Item Skeleton
export function MealItemSkeleton() {
  return (
    <div className="flex items-start gap-3 p-4 bg-white rounded-lg border border-slate-200">
      <Skeleton className="w-12 h-12 rounded-full flex-shrink-0" />
      <div className="flex-1 space-y-2">
        <div className="flex items-center justify-between">
          <Skeleton className="h-4 w-28" />
          <Skeleton className="h-4 w-16" />
        </div>
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-3 w-full" />
        <Skeleton className="h-3 w-2/3" />
      </div>
    </div>
  );
}

// Accommodation Skeleton
export function AccommodationSkeleton() {
  return (
    <div className="p-4 bg-white rounded-lg border border-slate-200">
      <div className="flex items-start gap-3">
        <Skeleton className="w-12 h-12 rounded-full flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <div className="flex items-center justify-between">
            <Skeleton className="h-5 w-40" />
            <Skeleton className="h-4 w-20" />
          </div>
          <Skeleton className="h-3 w-24" />
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-3/4" />
        </div>
      </div>
    </div>
  );
}

// Day Itinerary Skeleton
export function DayItinerarySkeleton() {
  return (
    <div className="space-y-6">
      {/* Activities Section */}
      <div className="space-y-4">
        <Skeleton className="h-6 w-32" />
        <div className="space-y-3">
          <ActivityItemSkeleton />
          <ActivityItemSkeleton />
          <ActivityItemSkeleton />
        </div>
      </div>

      {/* Meals Section */}
      <div className="space-y-4">
        <Skeleton className="h-6 w-24" />
        <div className="space-y-3">
          <MealItemSkeleton />
          <MealItemSkeleton />
          <MealItemSkeleton />
        </div>
      </div>

      {/* Accommodation Section */}
      <div className="space-y-4">
        <Skeleton className="h-6 w-32" />
        <AccommodationSkeleton />
      </div>
    </div>
  );
}

// Trip Summary Skeleton
export function TripSummarySkeleton() {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-4">
      <Skeleton className="h-6 w-40" />
      <div className="grid grid-cols-2 gap-4">
        <div className="space-y-2">
          <Skeleton className="h-4 w-20" />
          <Skeleton className="h-8 w-24" />
        </div>
        <div className="space-y-2">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-8 w-20" />
        </div>
      </div>
      <div className="space-y-2">
        <Skeleton className="h-4 w-32" />
        <div className="space-y-1">
          <Skeleton className="h-3 w-full" />
          <Skeleton className="h-3 w-3/4" />
          <Skeleton className="h-3 w-1/2" />
        </div>
      </div>
    </div>
  );
}

// Budget Tracker Skeleton
export function BudgetTrackerSkeleton() {
  return (
    <div className="bg-white rounded-lg border border-slate-200 p-6 space-y-4">
      <Skeleton className="h-6 w-32" />
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <Skeleton className="h-4 w-24" />
          <Skeleton className="h-6 w-20" />
        </div>
        <div className="space-y-2">
          <div className="flex justify-between">
            <Skeleton className="h-3 w-20" />
            <Skeleton className="h-3 w-16" />
          </div>
          <div className="flex justify-between">
            <Skeleton className="h-3 w-16" />
            <Skeleton className="h-3 w-12" />
          </div>
          <div className="flex justify-between">
            <Skeleton className="h-3 w-24" />
            <Skeleton className="h-3 w-14" />
          </div>
        </div>
      </div>
    </div>
  );
}

// Loading Button with Skeleton
export function LoadingButton({ isLoading, children, className, ...props }) {
  return (
    <button
      className={`flex items-center gap-2 ${className}`}
      disabled={isLoading}
      {...props}
    >
      {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
      {children}
    </button>
  );
}
