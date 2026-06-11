"use client"

import Link from "next/link"
import { ShieldCheck, Book, Code, Search, Home, LayoutDashboard, Shield, Settings, Activity } from "lucide-react"
import { Button } from "@/ports/ui/components/ui/button"
import { usePathname } from "next/navigation"
import { cn } from "@/ports/types/utils"
import { useState, useEffect } from "react"
import {
  NavigationMenu,
  NavigationMenuContent,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList,
  NavigationMenuTrigger,
} from '@/ports/ui/components/ui/navigation-menu'

export function Header() {
  const pathname = usePathname()
  // In a real app, this would come from an auth context
  const [isAuthenticated, setIsAuthenticated] = useState(false)

  useEffect(() => {
    // Mock authentication check
    const loggedIn = localStorage.getItem("isLoggedIn") === "true"
    setIsAuthenticated(loggedIn)
  }, [pathname])

  const navLinks = [
    { href: "/search", label: "Browse", icon: Search },
    { href: "#", label: "API Docs", icon: Code },
    { href: "#", label: "Blog", icon: Book },
  ]

  const handleLogout = () => {
    localStorage.removeItem("isLoggedIn")
    setIsAuthenticated(false)
    // In a real app, you'd also redirect or make an API call to log out
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center">
        <div className="mr-4 hidden md:flex">
          <Link href="/" className="mr-6 flex items-center space-x-2">
            <Shield className="h-6 w-6" />
            <span className="hidden font-bold sm:inline-block">
              SCAP etzhayyim.AI
            </span>
          </Link>
          <NavigationMenu>
            <NavigationMenuList>
              <NavigationMenuItem>
                <Link href="/" legacyBehavior passHref>
                  <NavigationMenuLink className="group inline-flex h-9 w-max items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[active]:bg-accent/50 data-[state=open]:bg-accent/50">
                    <Home className="mr-2 h-4 w-4" />
                    ホーム
                  </NavigationMenuLink>
                </Link>
              </NavigationMenuItem>

              <NavigationMenuItem>
                <Link href="/dashboard" legacyBehavior passHref>
                  <NavigationMenuLink className="group inline-flex h-9 w-max items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[active]:bg-accent/50 data-[state=open]:bg-accent/50">
                    <LayoutDashboard className="mr-2 h-4 w-4" />
                    ダッシュボード
                  </NavigationMenuLink>
                </Link>
              </NavigationMenuItem>

              <NavigationMenuItem>
                <Link href="/search" legacyBehavior passHref>
                  <NavigationMenuLink className="group inline-flex h-9 w-max items-center justify-center rounded-md bg-background px-4 py-2 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[active]:bg-accent/50 data-[state=open]:bg-accent/50">
                    <Search className="mr-2 h-4 w-4" />
                    検索
                  </NavigationMenuLink>
                </Link>
              </NavigationMenuItem>

              <NavigationMenuItem>
                <NavigationMenuTrigger>
                  <Settings className="mr-2 h-4 w-4" />
                  管理
                </NavigationMenuTrigger>
                <NavigationMenuContent>
                  <div className="grid w-[400px] gap-3 p-4 md:w-[500px] md:grid-cols-2 lg:w-[600px]">
                    <Link
                      href="/admin/workers"
                      className="group grid h-auto w-full justify-start gap-1 rounded-md bg-background p-4 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground focus:bg-accent focus:text-accent-foreground focus:outline-none disabled:pointer-events-none disabled:opacity-50 data-[active]:bg-accent/50 data-[state=open]:bg-accent/50"
                    >
                      <div className="flex items-center">
                        <Activity className="mr-2 h-4 w-4" />
                        ワーカー管理
                      </div>
                      <div className="line-clamp-2 text-xs leading-snug text-muted-foreground">
                        Workflow DevKitベースのワークフローの監視と制御
                      </div>
                    </Link>

                    <div className="group grid h-auto w-full justify-start gap-1 rounded-md bg-background p-4 text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground">
                      <div className="flex items-center">
                        <Shield className="mr-2 h-4 w-4" />
                        セキュリティ設定
                      </div>
                      <div className="line-clamp-2 text-xs leading-snug text-muted-foreground">
                        システムセキュリティの設定
                      </div>
                    </div>
                  </div>
                </NavigationMenuContent>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
        </div>

        <div className="flex flex-1 items-center justify-between space-x-2 md:justify-end">
          <div className="w-full flex-1 md:w-auto md:flex-none">
            {/* 検索バーを必要に応じて追加 */}
          </div>
          <nav className="flex items-center">
            <Button variant="outline" size="sm">
              ログイン
            </Button>
          </nav>
        </div>
      </div>
    </header>
  )
}
