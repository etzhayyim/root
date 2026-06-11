import { Header } from "@/components/layout/header"
import { Sidebar } from "@/components/layout/sidebar"
import { TransactionRules } from "@/components/rules-engine/transaction-rules"
import { NameScreeningRules } from "@/components/rules-engine/name-screening-rules"
import { CountryRiskRules } from "@/components/rules-engine/country-risk-rules"

export default function RulesEnginePage() {
  return (
    <div className="grid min-h-screen w-full md:grid-cols-[220px_1fr] lg:grid-cols-[280px_1fr]">
      <Sidebar />
      <div className="flex flex-col">
        <Header />
        <main className="flex flex-1 flex-col gap-4 p-4 md:gap-8 md:p-8 bg-muted/40">
          <div className="mx-auto grid w-full max-w-6xl gap-2">
            <h1 className="text-3xl font-semibold">Screening Rules Engine</h1>
            <p className="text-muted-foreground">
              Configure thresholds and parameters for the risk detection system. Changes are logged and will take effect
              immediately.
            </p>
          </div>
          <div className="mx-auto grid w-full max-w-6xl items-start gap-6 md:grid-cols-1 lg:grid-cols-2">
            <div className="grid gap-6">
              <TransactionRules />
              <NameScreeningRules />
            </div>
            <div className="grid gap-6">
              <CountryRiskRules />
              {/* Add more rule components here */}
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}
