import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuTrigger,
  DropdownMenuContent,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuCheckboxItem,
} from "@/components/ui/dropdown-menu"
import { ListFilter } from "lucide-react"
import Link from "next/link"

const cases = [
  {
    caseId: "CASE-021",
    customerName: "John Doe",
    priority: "High",
    status: "In Progress",
    assignee: "Alex Ray",
    lastUpdated: "2025-07-02",
    summary: "OFAC Sanctions Match",
  },
  {
    caseId: "CASE-022",
    customerName: "Alice Smith",
    priority: "High",
    status: "Open",
    assignee: "Unassigned",
    lastUpdated: "2025-07-02",
    summary: "Adverse Media Hits",
  },
  {
    caseId: "CASE-020",
    customerName: "Bob Johnson",
    priority: "Medium",
    status: "Resolved",
    assignee: "Bethany King",
    lastUpdated: "2025-07-01",
    summary: "Unusual Transaction Pattern",
  },
  {
    caseId: "CASE-019",
    customerName: "Eva Williams",
    priority: "Medium",
    status: "Resolved",
    assignee: "Alex Ray",
    lastUpdated: "2025-06-30",
    summary: "PEP Association",
  },
]

const getStatusBadgeVariant = (status: string) => {
  switch (status) {
    case "In Progress":
      return "secondary"
    case "Open":
      return "destructive"
    case "Resolved":
      return "default"
    default:
      return "outline"
  }
}

const getPriorityBadgeVariant = (priority: string) => {
  switch (priority) {
    case "High":
      return "destructive"
    case "Medium":
      return "secondary"
    default:
      return "outline"
  }
}

export function CaseListTable() {
  return (
    <div>
      <div className="flex items-center gap-2 mb-4">
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button variant="outline" size="sm" className="h-8 gap-1 bg-transparent">
              <ListFilter className="h-3.5 w-3.5" />
              <span className="sr-only sm:not-sr-only sm:whitespace-nowrap">Filter</span>
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuLabel>Filter by status</DropdownMenuLabel>
            <DropdownMenuSeparator />
            <DropdownMenuCheckboxItem checked>Open</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem>In Progress</DropdownMenuCheckboxItem>
            <DropdownMenuCheckboxItem>Resolved</DropdownMenuCheckboxItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Case ID</TableHead>
              <TableHead>Customer</TableHead>
              <TableHead>Priority</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Assignee</TableHead>
              <TableHead>Last Updated</TableHead>
              <TableHead>
                <span className="sr-only">Actions</span>
              </TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {cases.map((caseItem) => (
              <TableRow key={caseItem.caseId}>
                <TableCell className="font-medium">{caseItem.caseId}</TableCell>
                <TableCell>{caseItem.customerName}</TableCell>
                <TableCell>
                  <Badge
                    variant={getPriorityBadgeVariant(caseItem.priority)}
                    className={caseItem.priority === "Medium" ? "bg-yellow-400/80 text-yellow-900" : ""}
                  >
                    {caseItem.priority}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge
                    variant={getStatusBadgeVariant(caseItem.status)}
                    className={caseItem.status === "In Progress" ? "bg-blue-200 text-blue-800" : ""}
                  >
                    {caseItem.status}
                  </Badge>
                </TableCell>
                <TableCell>{caseItem.assignee}</TableCell>
                <TableCell>{caseItem.lastUpdated}</TableCell>
                <TableCell>
                  <Button asChild variant="outline" size="sm">
                    <Link href={`/cases/${caseItem.caseId}`}>Investigate</Link>
                  </Button>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </div>
    </div>
  )
}
