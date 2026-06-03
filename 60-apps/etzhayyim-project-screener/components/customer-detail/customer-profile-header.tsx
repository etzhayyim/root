import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Check, X, FolderPlus } from "lucide-react"

type Customer = {
  id: string
  name: string
  riskScore: number
  riskLevel: "High" | "Medium" | "Low"
  status: string
  joinDate: string
}

interface CustomerProfileHeaderProps {
  customer: Customer
}

export function CustomerProfileHeader({ customer }: CustomerProfileHeaderProps) {
  const getRiskColor = () => {
    if (customer.riskLevel === "High") return "bg-red-500"
    if (customer.riskLevel === "Medium") return "bg-yellow-500"
    return "bg-green-500"
  }

  return (
    <Card>
      <CardHeader>
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-4">
              <CardTitle className="text-2xl">{customer.name}</CardTitle>
              <Badge variant={customer.riskLevel === "High" ? "destructive" : "secondary"}>
                {customer.riskLevel} Risk
              </Badge>
            </div>
            <CardDescription>
              Customer ID: {customer.id} | Member since: {customer.joinDate}
            </CardDescription>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="outline">
              <FolderPlus className="mr-2 h-4 w-4" />
              Create Case
            </Button>
            <Button variant="outline" className="bg-green-100 hover:bg-green-200 text-green-800">
              <Check className="mr-2 h-4 w-4" />
              Approve
            </Button>
            <Button variant="destructive">
              <X className="mr-2 h-4 w-4" />
              Reject
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-center gap-4">
          <div className="text-sm font-medium">Overall Risk Score:</div>
          <div className="relative w-full max-w-sm h-2 bg-muted rounded-full">
            <div
              className={`absolute top-0 left-0 h-2 rounded-full ${getRiskColor()}`}
              style={{ width: `${customer.riskScore}%` }}
            ></div>
          </div>
          <div className="text-lg font-bold">{customer.riskScore} / 100</div>
        </div>
      </CardContent>
    </Card>
  )
}
