import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { FileText, User, AlertTriangle } from "lucide-react"
import Link from "next/link"

interface CaseEvidencePanelProps {
  customerId: string
}

export function CaseEvidencePanel({ customerId }: CaseEvidencePanelProps) {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Evidence & Links</CardTitle>
        <CardDescription>Relevant information for this case.</CardDescription>
      </CardHeader>
      <CardContent className="grid gap-4">
        <div className="flex items-start gap-4 rounded-md border p-4">
          <User className="mt-1 h-4 w-4" />
          <div className="grid gap-1">
            <p className="font-semibold">Customer Profile</p>
            <p className="text-sm text-muted-foreground">View the full profile of the customer under investigation.</p>
            <Button asChild variant="outline" size="sm" className="mt-2 w-fit bg-transparent">
              <Link href={`/customers/${customerId}`}>View Profile</Link>
            </Button>
          </div>
        </div>
        <div className="flex items-start gap-4 rounded-md border p-4">
          <AlertTriangle className="mt-1 h-4 w-4 text-red-500" />
          <div className="grid gap-1">
            <p className="font-semibold">Original Alert</p>
            <p className="text-sm text-muted-foreground">OFAC Sanctions Match (98% confidence).</p>
          </div>
        </div>
        <div className="flex items-start gap-4 rounded-md border p-4">
          <FileText className="mt-1 h-4 w-4" />
          <div className="grid gap-1">
            <p className="font-semibold">Attached Documents</p>
            <p className="text-sm text-muted-foreground">No documents attached yet.</p>
            <Button variant="outline" size="sm" className="mt-2 w-fit bg-transparent">
              Upload Document
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
