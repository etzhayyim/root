import { Header } from "@/components/layout/header"
import { Sidebar } from "@/components/layout/sidebar"
import { CaseDetailHeader } from "@/components/case-management/case-detail-header"
import { CaseInvestigationPanel } from "@/components/case-management/case-investigation-panel"
import { CaseEvidencePanel } from "@/components/case-management/case-evidence-panel"

// Mock data for a single case
const MOCK_CASE_DATA = {
  caseId: "CASE-021",
  customerId: "CUST-001",
  customerName: "John Doe",
  status: "In Progress",
  priority: "High",
  assignee: "Alex Ray",
  createdAt: "2025-07-02",
  summary: "OFAC Sanctions Match with 98% confidence.",
}

export default function CaseDetailPage({ params }: { params: { caseId: string } }) {
  const caseData = { ...MOCK_CASE_DATA, caseId: params.caseId }

  return (
    <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
      <Sidebar />
      <div className="flex flex-col">
        <Header />
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8 bg-muted/40">
          <CaseDetailHeader caseData={caseData} />
          <div className="grid gap-4 md:gap-8 lg:grid-cols-3">
            <div className="lg:col-span-2 grid auto-rows-max gap-4">
              <CaseInvestigationPanel />
            </div>
            <div className="lg:col-span-1 grid auto-rows-max gap-4">
              <CaseEvidencePanel customerId={caseData.customerId} />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
