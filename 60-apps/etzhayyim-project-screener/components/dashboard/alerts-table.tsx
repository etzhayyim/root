import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowUpRight } from "lucide-react"
import Link from "next/link"

const alerts = [
  {
    id: "CUST-001",
    name: "John Doe",
    risk: "High",
    source: "Sanctions List",
    date: "2025-07-02",
  },
  {
    id: "CUST-015",
    name: "Alice Smith",
    risk: "High",
    source: "Adverse Media",
    date: "2025-07-02",
  },
  {
    id: "TXN-987",
    name: "Bob Johnson",
    risk: "Medium",
    source: "Transaction Monitoring",
    date: "2025-07-01",
  },
  {
    id: "CUST-102",
    name: "Eva Williams",
    risk: "Medium",
    source: "PEP Screening",
    date: "2025-06-30",
  },
  {
    id: "CUST-042",
    name: "Michael Brown",
    risk: "Low",
    source: "IP Address",
    date: "2025-06-29",
  },
]

export function AlertsTable() {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center">
        <div className="grid gap-2">
          <CardTitle>Recent High-Priority Alerts</CardTitle>
          <CardDescription>Alerts requiring immediate attention.</CardDescription>
        </div>
        <Button asChild size="sm" className="ml-auto gap-1">
          <Link href="#">
            View All
            <ArrowUpRight className="h-4 w-4" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Customer/Txn ID</TableHead>
              <TableHead>Name</TableHead>
              <TableHead>Risk Level</TableHead>
              <TableHead>Source</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>
                <span className="sr-only">Actions</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {alerts.map((alert) => (
              <TableRow key={alert.id} className="hover:bg-muted/50">
                <TableCell className="font-medium">{alert.id}</TableCell>
                <TableCell>{alert.name}</TableCell>
                <TableCell>
                  <Badge
                    variant={alert.risk === "High" ? "destructive" : alert.risk === "Medium" ? "secondary" : "outline"}
                    className={alert.risk === "Medium" ? "bg-yellow-400/80 text-yellow-900" : ""}
                  >
                    {alert.risk}
                  </Badge>
                </TableCell>
                <TableCell>{alert.source}</TableCell>
                <TableCell>{alert.date}</TableCell>
                <TableCell>
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/customers/${alert.id}`}>View Details</Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
