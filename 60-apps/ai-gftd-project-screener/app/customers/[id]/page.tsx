import { Header } from "@/components/layout/header"
import { Sidebar } from "@/components/layout/sidebar"
import { CustomerProfileHeader } from "@/components/customer-detail/customer-profile-header"
import { ScreeningDetailsTabs } from "@/components/customer-detail/screening-details-tabs"
import { TransactionHistory } from "@/components/customer-detail/transaction-history"
import { AuditTrail } from "@/components/customer-detail/audit-trail"

// In a real app, you would fetch this data from your API based on the `params.id`
const MOCK_CUSTOMER_DATA = {
  id: "CUST-001",
  name: "John Doe",
  riskScore: 95,
  riskLevel: "High",
  status: "Pending Review",
  joinDate: "2025-01-15",
  email: "john.doe@example.com",
  address: "123 Main St, Anytown, USA",
}

export default function CustomerDetailPage({ params }: { params: { id: string } }) {
  // You can use params.id to fetch specific customer data
  const customerData = { ...MOCK_CUSTOMER_DATA, id: params.id }

  return (
    <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
      <Sidebar />
      <div className="flex flex-col">
        <Header />
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8 bg-muted/40">
          <CustomerProfileHeader customer={customerData} />
          <div className="grid gap-4 md:gap-8 lg:grid-cols-3">
            <div className="lg:col-span-2 grid auto-rows-max gap-4">
              <ScreeningDetailsTabs />
              <TransactionHistory />
            </div>
            <div className="lg:col-span-1 grid auto-rows-max gap-4">
              <AuditTrail />
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
