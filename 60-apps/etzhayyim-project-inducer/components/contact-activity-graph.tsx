"use client"

import { Bar, BarChart, ResponsiveContainer, XAxis, YAxis, Tooltip } from "recharts"
import { ChartContainer, ChartTooltipContent } from "@/components/ui/chart"

const chartData = [
  { date: "2025-06-01", engagement: 10 },
  { date: "2025-06-02", engagement: 15 },
  { date: "2025-06-03", engagement: 12 },
  { date: "2025-06-04", engagement: 35 },
  { date: "2025-06-05", engagement: 40 },
  { date: "2025-06-06", engagement: 85 },
  { date: "2025-06-07", engagement: 82 },
]

const chartConfig = {
  engagement: {
    label: "Engagement Score",
    color: "hsl(var(--chart-1))",
  },
}

export default function ContactActivityGraph() {
  return (
    <div className="h-[300px] w-full">
      <ChartContainer config={chartConfig}>
        <ResponsiveContainer width="100%" height="100%">
          <BarChart data={chartData} margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
            <XAxis dataKey="date" tickLine={false} axisLine={false} stroke="#888888" fontSize={12} />
            <YAxis tickLine={false} axisLine={false} stroke="#888888" fontSize={12} />
            <Tooltip content={<ChartTooltipContent />} cursor={{ fill: "hsl(var(--muted))" }} />
            <Bar dataKey="engagement" fill="var(--color-engagement)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </ChartContainer>
    </div>
  )
}
