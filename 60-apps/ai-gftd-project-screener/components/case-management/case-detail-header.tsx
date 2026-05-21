import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { User, ArrowRight } from "lucide-react"

interface CaseDetailHeaderProps {
  caseData: {
    caseId: string
    customerName: string
    status: string
    priority: string
    assignee: string
  }
}

export function CaseDetailHeader({ caseData }: CaseDetailHeaderProps) {
  return (
    <div className="flex items-center justify-between gap-4 flex-wrap">
      <div className="grid gap-1">
        <h1 className="text-2xl font-bold tracking-tight flex items-center gap-2">
          Case: {caseData.caseId}
          <Badge
            variant={caseData.priority === "High" ? "destructive" : "secondary"}
            className={caseData.priority === "Medium" ? "bg-yellow-400/80 text-yellow-900" : ""}
          >
            {caseData.priority} Priority
          </Badge>
        </h1>
        <p className="text-muted-foreground">
          Investigating customer: <span className="font-semibold text-primary">{caseData.customerName}</span>
        </p>
      </div>
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 text-sm text-muted-foreground">
          <User className="h-4 w-4" />
          Assigned to: <span className="font-semibold text-foreground">{caseData.assignee}</span>
        </div>
        <Button>
          Escalate Case <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </div>
    </div>
  )
}
