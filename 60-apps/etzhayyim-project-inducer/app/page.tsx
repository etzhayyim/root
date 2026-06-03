import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card"
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from "@/components/ui/table"
import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import Link from "next/link"
import { Activity, DollarSign, Users, Bot } from "lucide-react"

export default function DashboardPage() {
  const prospects = [
    {
      id: "1",
      name: "Alice Johnson",
      email: "alice@example.com",
      status: "Engaging",
      stage: "Interest",
      lastActivity: "Clicked pricing link",
      agent: "Email Bot",
    },
    {
      id: "2",
      name: "Bob Williams",
      email: "bob@example.com",
      status: "Needs Review",
      stage: "Consideration",
      lastActivity: "Replied to email",
      agent: "Human takeover",
    },
    {
      id: "3",
      name: "Charlie Brown",
      email: "charlie@example.com",
      status: "Idle",
      stage: "Awareness",
      lastActivity: "Visited landing page",
      agent: "N/A",
    },
    {
      id: "4",
      name: "Diana Miller",
      email: "diana@example.com",
      status: "Engaging",
      stage: "Interest",
      lastActivity: "Opened 3rd email",
      agent: "Email Bot",
    },
  ]

  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/40">
      <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8">
        <div className="grid gap-4 md:grid-cols-2 md:gap-8 lg:grid-cols-4">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Revenue</CardTitle>
              <DollarSign className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">$45,231.89</div>
              <p className="text-xs text-muted-foreground">+20.1% from last month</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Contacts</CardTitle>
              <Users className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">+2350</div>
              <p className="text-xs text-muted-foreground">+180.1% from last month</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Engagement Rate</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">62.4%</div>
              <p className="text-xs text-muted-foreground">+19% from last month</p>
            </CardContent>
          </Card>
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">AI Agents Active</CardTitle>
              <Bot className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">4</div>
              <p className="text-xs text-muted-foreground">Email, SNS, Ad, Web</p>
            </CardContent>
          </Card>
        </div>
        <Card>
          <CardHeader>
            <CardTitle>Active Prospects</CardTitle>
            <CardDescription>
              List of contacts currently being engaged by AI agents or requiring attention.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Customer</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Stage</TableHead>
                  <TableHead>Last Activity</TableHead>
                  <TableHead>Assigned Agent</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {prospects.map((prospect) => (
                  <TableRow key={prospect.id}>
                    <TableCell>
                      <Link href={`/contacts/${prospect.id}`} className="hover:underline">
                        <div className="flex items-center gap-2">
                          <Avatar>
                            <AvatarImage src={`https://avatar.vercel.sh/${prospect.email}.png`} />
                            <AvatarFallback>{prospect.name.charAt(0)}</AvatarFallback>
                          </Avatar>
                          <div className="font-medium">{prospect.name}</div>
                        </div>
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Badge variant={prospect.status === "Needs Review" ? "destructive" : "secondary"}>
                        {prospect.status}
                      </Badge>
                    </TableCell>
                    <TableCell>{prospect.stage}</TableCell>
                    <TableCell>{prospect.lastActivity}</TableCell>
                    <TableCell>{prospect.agent}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </main>
    </div>
  )
}
