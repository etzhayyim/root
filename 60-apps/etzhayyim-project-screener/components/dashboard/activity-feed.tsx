import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

const activities = [
  { user: "Alex Ray", action: "cleared alert for", target: "CUST-089", time: "5m ago", initials: "AR" },
  { user: "System", action: "detected high-risk transaction", target: "TXN-1052", time: "15m ago", initials: "S" },
  { user: "Bethany King", action: "escalated case", target: "CASE-021", time: "45m ago", initials: "BK" },
  { user: "System", action: "ran hourly PEP screening", target: "", time: "1h ago", initials: "S" },
  {
    user: "Charles Davis",
    action: "updated screening rule",
    target: "'High-Value Cash Deposits'",
    time: "3h ago",
    initials: "CD",
  },
]

export function ActivityFeed() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Activity</CardTitle>
        <CardDescription>Live feed of system and user actions.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-6">
        {activities.map((activity, index) => (
          <div key={index} className="flex items-center gap-4">
            <Avatar className="hidden h-9 w-9 sm:flex">
              <AvatarFallback>{activity.initials}</AvatarFallback>
            </Avatar>
            <div className="grid gap-1">
              <p className="text-sm font-medium leading-none">
                <span className="font-semibold">{activity.user}</span> {activity.action}{" "}
                <span className="font-semibold text-primary">{activity.target}</span>
              </p>
              <p className="text-sm text-muted-foreground">{activity.time}</p>
            </div>
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
