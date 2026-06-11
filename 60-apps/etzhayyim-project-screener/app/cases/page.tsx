import { Header } from "@/components/layout/header"
import { Sidebar } from "@/components/layout/sidebar"
import { CaseListTable } from "@/components/case-management/case-list-table"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"

export default function CaseManagementPage() {
  return (
    <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
      <Sidebar />
      <div className="flex flex-col">
        <Header />
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8 bg-muted/40">
          <Card>
            <CardHeader>
              <CardTitle className="text-2xl">Case Management</CardTitle>
              <CardDescription>Track, investigate, and resolve all open and closed cases.</CardDescription>
            </CardHeader>
            <CardContent>
              <CaseListTable />
            </CardContent>
          </Card>
        </main>
      </div>
    </div>
  )
}
