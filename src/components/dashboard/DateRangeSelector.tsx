import React, { useState, useEffect } from "react";
import { CalendarIcon } from "lucide-react";
import { format } from "date-fns";
import { Button } from "@/components/ui/button";
import { Calendar } from "@/components/ui/calendar";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";

interface DateRangeSelectorProps {
  onRangeChange: (range: { from: Date; to: Date; type: string }) => void;
  defaultRange?: string;
}

export function DateRangeSelector({ onRangeChange, defaultRange = "24h" }: DateRangeSelectorProps) {
  const [selectedRange, setSelectedRange] = useState(defaultRange);
  const [customDateFrom, setCustomDateFrom] = useState<Date>();
  const [customDateTo, setCustomDateTo] = useState<Date>();
  const [isCustomOpen, setIsCustomOpen] = useState(false);

  const predefinedRanges = [
    { value: "24h", label: "Last 24 Hours" },
    { value: "2d", label: "Last 2 Days" },
    { value: "7d", label: "Last 7 Days" },
    { value: "30d", label: "Last 30 Days" },
    { value: "custom", label: "Custom Range" }
  ];

  // Trigger initial callback on mount to sync parent state
  useEffect(() => {
    handleRangeSelect(defaultRange);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const handleRangeSelect = (value: string) => {
    setSelectedRange(value);
    
    if (value !== "custom") {
      const now = new Date();
      const from = new Date(now);
      
      switch (value) {
        case "24h":
          from.setHours(from.getHours() - 24);
          break;
        case "2d":
          from.setDate(from.getDate() - 2);
          break;
        case "7d":
          from.setDate(from.getDate() - 7);
          break;
        case "30d":
          from.setDate(from.getDate() - 30);
          break;
      }
      
      onRangeChange({ from, to: now, type: value });
    }
  };

  const handleCustomRangeApply = () => {
    if (customDateFrom && customDateTo) {
      onRangeChange({ 
        from: customDateFrom, 
        to: customDateTo, 
        type: "custom" 
      });
      setIsCustomOpen(false);
    }
  };

  return (
    <div className="flex gap-2 items-center">
      <Select value={selectedRange} onValueChange={handleRangeSelect}>
        <SelectTrigger className="w-40">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {predefinedRanges.map((range) => (
            <SelectItem key={range.value} value={range.value}>
              {range.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {selectedRange === "custom" && (
        <Popover open={isCustomOpen} onOpenChange={setIsCustomOpen}>
          <PopoverTrigger asChild>
            <Button
              variant="outline"
              className={cn(
                "justify-start text-left font-normal",
                (!customDateFrom || !customDateTo) && "text-muted-foreground"
              )}
            >
              <CalendarIcon className="mr-2 h-4 w-4" />
              {customDateFrom && customDateTo ? (
                `${format(customDateFrom, "MMM dd")} - ${format(customDateTo, "MMM dd")}`
              ) : (
                "Pick dates"
              )}
            </Button>
          </PopoverTrigger>
          <PopoverContent className="w-auto p-0" align="start">
            <div className="flex">
              <div className="p-3">
                <p className="text-sm font-medium mb-2">From</p>
                <Calendar
                  mode="single"
                  selected={customDateFrom}
                  onSelect={setCustomDateFrom}
                  className="pointer-events-auto"
                />
              </div>
              <div className="p-3 border-l">
                <p className="text-sm font-medium mb-2">To</p>
                <Calendar
                  mode="single"
                  selected={customDateTo}
                  onSelect={setCustomDateTo}
                  className="pointer-events-auto"
                />
              </div>
            </div>
            <div className="p-3 border-t flex justify-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() => setIsCustomOpen(false)}
              >
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleCustomRangeApply}
                disabled={!customDateFrom || !customDateTo}
              >
                Apply
              </Button>
            </div>
          </PopoverContent>
        </Popover>
      )}
    </div>
  );
}