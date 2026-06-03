import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"

const transactions = [
  { id: "TXN-1052", date: "2025-07-01", amount: "$15,000.00", type: "Incoming Wire", status: "Flagged" },
  { id: "TXN-1048", date: "2025-06-28", amount: "$2,500.00", type: "Card Purchase", status: "Cleared" },
  { id: "TXN-1045", date: "2025-06-25", amount: "$800.00", type: "ATM Withdrawal", status: "Cleared" },
  { id: "TXN-1041", date: "2025-06-22", amount: "$12,000.00", type: "Incoming Wire", status: "Flagged" },
]

export function TransactionHistory() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Transaction History</CardTitle>
        <CardDescription>Recent transactions associated with this customer.</CardDescription>
      </CardHeader>
      <CardContent>
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>Transaction ID</TableHead>
              <TableHead>Date</TableHead>
              <TableHead>Amount</TableHead>
              <TableHead>Type</TableHead>
              <TableHead>Status</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {transactions.map((tx) => (
              <TableRow key={tx.id}>
                <TableCell className="font-medium">{tx.id}</TableCell>
                <TableCell>{tx.date}</TableCell>
                <TableCell>{tx.amount}</TableCell>
                <TableCell>{tx.type}</TableCell>
                <TableCell>
                  <Badge variant={tx.status === "Flagged" ? "destructive" : "outline"}>{tx.status}</Badge>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
