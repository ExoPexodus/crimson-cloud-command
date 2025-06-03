
import { InstancePoolCard } from "@/components/dashboard/InstancePoolCard";
import { useToast } from "@/hooks/use-toast";

// Mock data for recently active pools (will be replaced with real data later)
const recentInstancePools = [
  {
    id: "pool-1",
    name: "Production API Pool",
    instances: 4,
    maxInstances: 8,
    status: "healthy" as const,
    region: "US West (Phoenix)",
    cpuUsage: 62,
    memoryUsage: 48,
  },
  {
    id: "pool-2",
    name: "ML Training Workers",
    instances: 6,
    maxInstances: 10,
    status: "warning" as const,
    region: "US East (Ashburn)",
    cpuUsage: 78,
    memoryUsage: 65,
  },
  {
    id: "pool-3",
    name: "Database Cluster",
    instances: 3,
    maxInstances: 5,
    status: "healthy" as const,
    region: "Europe (Frankfurt)",
    cpuUsage: 45,
    memoryUsage: 72,
  },
  {
    id: "pool-4",
    name: "Dev Environment",
    instances: 1,
    maxInstances: 3,
    status: "inactive" as const,
    region: "Asia Pacific (Tokyo)",
    cpuUsage: 12,
    memoryUsage: 25,
  }
];

export function InstancePoolsSection() {
  const { toast } = useToast();

  return (
    <div>
      <h2 className="text-lg font-medium mb-4">Recently Active Instance Pools</h2>
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {recentInstancePools.map((pool) => (
          <InstancePoolCard
            key={pool.id}
            name={pool.name}
            instances={pool.instances}
            maxInstances={pool.maxInstances}
            status={pool.status}
            region={pool.region}
            cpuUsage={pool.cpuUsage}
            memoryUsage={pool.memoryUsage}
            onScaleUp={() => toast({ title: "Scale Up", description: `Scaling up ${pool.name}` })}
            onScaleDown={() => toast({ title: "Scale Down", description: `Scaling down ${pool.name}` })}
          />
        ))}
      </div>
    </div>
  );
}
