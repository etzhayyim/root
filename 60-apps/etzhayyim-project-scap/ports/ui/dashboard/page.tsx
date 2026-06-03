"use client"

import { useQuery } from "@apollo/client"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/ports/ui/components/ui/card"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/ports/ui/components/ui/table"
import { Badge } from "@/ports/ui/components/ui/badge"
import { FileText, AlertTriangle, ListChecks, KeyRound, Copy, Check } from "lucide-react"
import { Button } from "@/ports/ui/components/ui/button"
import { Input } from "@/ports/ui/components/ui/input"
import { useState } from "react"
import { gql } from "@apollo/client"

const DASHBOARD_STATS = gql`
  query DashboardStats {
    dashboardStats {
      ovalDefinitions
      xccdfBenchmarks
      highSeverityCves
      recentActivity {
        id
        type
        title
        lastUpdated
      }
    }
  }
`

// This is a client component because it uses state for the copy button

export default function DashboardPage() {
  const apiKey = "scap_live_demo_a3b8c7d6e5f4a1b2c3d4e5f6"
  const [hasCopied, setHasCopied] = useState(false)

  // GraphQL query for dashboard stats
  const { data, loading, error } = useQuery(DASHBOARD_STATS)

  const dashboardStats = data?.dashboardStats
  const recentActivity = dashboardStats?.recentActivity || []

  const copyToClipboard = () => {
    navigator.clipboard.writeText(apiKey)
    setHasCopied(true)
    setTimeout(() => setHasCopied(false), 2000)
  }

  return (
    <div className="grid gap-4 md:gap-8">
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">OVAL Definitions</CardTitle>
            <FileText className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : dashboardStats?.ovalDefinitions?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">+201 from last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">XCCDF Benchmarks</CardTitle>
            <ListChecks className="w-4 h-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : dashboardStats?.xccdfBenchmarks?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">+15 from last month</p>
          </CardContent>
        </Card>
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2 space-y-0">
            <CardTitle className="text-sm font-medium">High-Severity CVEs</CardTitle>
            <AlertTriangle className="w-4 h-4 text-destructive" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">
              {loading ? '...' : dashboardStats?.highSeverityCves?.toLocaleString() || '0'}
            </div>
            <p className="text-xs text-muted-foreground">Tracked via OVAL definitions</p>
          </CardContent>
        </Card>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>API Key Management</CardTitle>
          <CardDescription>Use this key to authenticate your API requests.</CardDescription>
        </CardHeader>
        <CardContent className="flex items-center gap-4">
          <KeyRound className="w-6 h-6 text-muted-foreground" />
          <Input readOnly value={apiKey} className="font-mono" />
          <Button variant="outline" size="icon" onClick={copyToClipboard}>
            {hasCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
            <span className="sr-only">Copy API Key</span>
          </Button>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
          <CardDescription>Latest SCAP content additions and updates from the event stream.</CardDescription>
        </CardHeader>
        <CardContent>
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Content ID</TableHead>
                <TableHead>Type</TableHead>
                <TableHead>Title</TableHead>
                <TableHead>Event Time</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {loading ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    読み込み中...
                  </TableCell>
                </TableRow>
              ) : error ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-destructive">
                    エラー: {error.message}
                  </TableCell>
                </TableRow>
              ) : recentActivity.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} className="text-center text-muted-foreground">
                    最近のアクティビティがありません
                  </TableCell>
                </TableRow>
              ) : (
                recentActivity.map((item: any) => (
                  <TableRow key={item.id}>
                    <TableCell className="font-mono text-xs">{item.id}</TableCell>
                    <TableCell>
                      <Badge variant={item.type.toLowerCase() === "oval" ? "default" : item.type.toLowerCase() === "xccdf" ? "secondary" : "outline"}>
                        {item.type}
                      </Badge>
                    </TableCell>
                    <TableCell className="font-medium">{item.title}</TableCell>
                    <TableCell>{new Date(item.lastUpdated).toLocaleString('ja-JP')}</TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </div>
  )
}
