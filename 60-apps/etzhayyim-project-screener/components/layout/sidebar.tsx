import Link from "next/link"
import { Home, Users, FileText, LineChart, Settings, Shield, Package } from "lucide-react"
import { Badge } from "@/components/ui/badge"

export function Sidebar() {
  return (
    <div className="hidden border-r bg-background md:block">
      <div className="flex h-full max-h-screen flex-col gap-2">
        <div className="flex h-14 items-center border-b px-4 lg:h-[60px] lg:px-6">
          <Link href="/" className="flex items-center gap-2 font-semibold">
            <Shield className="h-6 w-6 text-primary" />
            <span className="">RiskGuard AI</span>
          </Link>
        </div>
        <div className="flex-1">
          <nav className="grid items-start px-2 text-sm font-medium lg:px-4">
            <Link
              href="/"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <Home className="h-4 w-4" />
              Dashboard
            </Link>
            <Link
              href="#"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <Users className="h-4 w-4" />
              Customers
            </Link>
            <Link
              href="/cases"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <FileText className="h-4 w-4" />
              Case Management
              <Badge className="ml-auto flex h-6 w-6 shrink-0 items-center justify-center rounded-full">32</Badge>
            </Link>
            <Link
              href="#"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary"
            >
              <LineChart className="h-4 w-4" />
              Reports
            </Link>
          </nav>
        </div>
        <div className="mt-auto p-4">
          <div className="grid gap-2">
            <p className="text-xs text-muted-foreground font-semibold">SETTINGS</p>
            <Link
              href="/settings/rules"
              className="flex items-center gap-3 rounded-lg bg-muted px-3 py-2 text-primary transition-all hover:text-primary text-sm"
            >
              <Package className="h-4 w-4" />
              Screening Rules
            </Link>
            <Link
              href="#"
              className="flex items-center gap-3 rounded-lg px-3 py-2 text-muted-foreground transition-all hover:text-primary text-sm"
            >
              <Settings className="h-4 w-4" />
              System Settings
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
