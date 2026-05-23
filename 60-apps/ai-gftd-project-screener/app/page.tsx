import { Header } from "@/components/layout/header"
import { Sidebar } from "@/components/layout/sidebar"
import { SummaryCard } from "@/components/dashboard/summary-card"
import { AlertsTable } from "@/components/dashboard/alerts-table"
import { RiskOverviewChart } from "@/components/dashboard/risk-overview-chart"
import { ActivityFeed } from "@/components/dashboard/activity-feed"
import { ScreeningStatus } from "@/components/dashboard/screening-status"
import { FileWarning, AlertTriangle, ShieldCheck, Search } from "lucide-react"

export default function DashboardPage() {
  return (
    <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
      <Sidebar />
      <div className="flex flex-col">
        <Header />
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8 bg-muted/40">
          <div className="grid gap-4 md:grid-cols-2 md:gap-8 lg:grid-cols-4">
            <SummaryCard
              title="High-Risk Alerts"
              value="58"
              change="+15.2%"
              changeType="increase"
              icon={AlertTriangle}
              iconColor="text-red-500"
            />
            <SummaryCard
              title="Cases Under Review"
              value="32"
              change="-5.1%"
              changeType="decrease"
              icon={FileWarning}
              iconColor="text-yellow-500"
            />
            <SummaryCard
              title="Total Screened"
              value="12,890"
              change="+2.5%"
              changeType="increase"
              icon={Search}
              iconColor="text-blue-500"
            />
            <SummaryCard
              title="Cleared Cases"
              value="1,230"
              change="+8.0%"
              changeType="increase"
              icon={ShieldCheck}
              iconColor="text-green-500"
            />
          </div>
          <div className="grid gap-4 md:gap-8 lg:grid-cols-2 xl:grid-cols-3">
            <div className="xl:col-span-2 grid auto-rows-max gap-4">
              <ScreeningStatus />
              <AlertsTable />
            </div>
            <div className="grid auto-rows-max gap-4">
              <RiskOverviewChart />
              <ActivityFeed />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
