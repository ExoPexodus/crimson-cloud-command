
import { LineChart, Line, XAxis, YAxis, CartesianGrid, ResponsiveContainer, Tooltip as RechartsTooltip } from "recharts";

interface MetricsChartProps {
  data: Array<{ name: string; value: number }>;
  title: string;
  valuePrefix?: string;
  valueSuffix?: string;
  color?: string;
}

export function MetricsChart({ 
  data,
  title,
  valuePrefix = "",
  valueSuffix = "",
  color = "#20B2AA"  
}: MetricsChartProps) {
  return (
    <div className="p-4 rounded-lg glass-card h-full flex flex-col">
      <div className="flex justify-between items-center mb-4">
        <h3 className="font-medium text-sm">{title}</h3>
        <span className="text-xs text-muted-foreground">Last 24 hours</span>
      </div>
      
      <div className="flex-1 min-h-[150px]">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data} margin={{ top: 5, right: 5, left: -20, bottom: 5 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="#2D3748" opacity={0.5} vertical={false} />
            <XAxis 
              dataKey="name" 
              stroke="#666" 
              tick={{ fill: '#999', fontSize: 10 }} 
              tickLine={{ stroke: '#666' }}
            />
            <YAxis 
              stroke="#666" 
              tick={{ fill: '#999', fontSize: 10 }}
              tickLine={{ stroke: '#666' }}
              tickFormatter={(value) => `${valuePrefix}${value}${valueSuffix}`}
            />
            <RechartsTooltip 
              contentStyle={{ 
                backgroundColor: '#1A202C', 
                borderColor: '#2D3748',
                borderRadius: '4px',
                boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
              }} 
              formatter={(value: number) => [`${valuePrefix}${value}${valueSuffix}`, title]}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke={color}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4, fill: color, stroke: '#1A202C' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
