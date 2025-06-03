
import { MetricsChart } from "@/components/dashboard/MetricsChart";

// Mock data for 24-hour metrics (will be enhanced with real data)
const poolActivityData = [
  { name: "00:00", value: 8 },
  { name: "04:00", value: 6 },
  { name: "08:00", value: 12 },
  { name: "12:00", value: 15 },
  { name: "16:00", value: 18 },
  { name: "20:00", value: 14 },
  { name: "24:00", value: 10 }
];

const instanceCountData = [
  { name: "00:00", value: 18 },
  { name: "04:00", value: 12 },
  { name: "08:00", value: 24 },
  { name: "12:00", value: 28 },
  { name: "16:00", value: 32 },
  { name: "20:00", value: 26 },
  { name: "24:00", value: 20 }
];

export function MetricsChartsSection() {
  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
      <MetricsChart
        data={poolActivityData}
        title="Active Pools"
        color="#20B2AA"
      />
      <MetricsChart
        data={instanceCountData}
        title="Total Instances"
        color="#16A085"
      />
    </div>
  );
}
