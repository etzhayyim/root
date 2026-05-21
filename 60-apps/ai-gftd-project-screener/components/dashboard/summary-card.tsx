import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import type { LucideIcon } from "lucide-react"
import { cn } from "@/lib/utils"

interface SummaryCardProps {
  title: string
  value: string
  change: string
  changeType: "increase" | "decrease"
  icon: LucideIcon
  iconColor?: string
}

export function SummaryCard({ title, value, change, changeType, icon: Icon, iconColor }: SummaryCardProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
        <CardTitle className="text-sm font-medium">{title}</CardTitle>
        <Icon className={cn("h-4 w-4 text-muted-foreground", iconColor)} />
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{value}</div>
        <p
          className={cn("text-xs text-muted-foreground", changeType === "increase" ? "text-green-600" : "text-red-600")}
        >
          {change} from last month
        </p>
      </CardContent>
    </Card>
  )
}
