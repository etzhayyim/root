import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { CheckCircle2, XCircle, Clock } from "lucide-react"

const screeningServices = [
  { name: "Sanctions Screening", status: "Operational", icon: CheckCircle2, color: "text-green-500" },
  { name: "PEP Screening", status: "Operational", icon: CheckCircle2, color: "text-green-500" },
  { name: "Adverse Media", status: "Operational", icon: CheckCircle2, color: "text-green-500" },
  { name: "Transaction Monitoring", status: "Degraded Performance", icon: Clock, color: "text-yellow-500" },
  { name: "Crypto Wallet Screening", status: "Operational", icon: CheckCircle2, color: "text-green-500" },
  { name: "IP/Device Intelligence", status: "Outage", icon: XCircle, color: "text-red-500" },
]

export function ScreeningStatus() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Screening Services Status</CardTitle>
        <CardDescription>Real-time status of all screening modules.</CardDescription>
      </CardHeader>
      <CardContent className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {screeningServices.map((service) => {
          const Icon = service.icon
          return (
            <div key={service.name} className="flex items-center gap-3 p-2 rounded-md bg-muted/50">
              <Icon className={`h-5 w-5 ${service.color}`} />
              <div>
                <p className="text-sm font-medium">{service.name}</p>
                <p className={`text-xs ${service.color}`}>{service.status}</p>
              </div>
            </div>
          )
        })}
      </CardContent>
    </Card>
  )
}
