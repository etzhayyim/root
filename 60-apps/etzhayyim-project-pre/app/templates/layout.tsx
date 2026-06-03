import Link from "next/link";
import { KeyRound, UserX, FileWarning } from 'lucide-react';

// このコンポーネントは 'use client' を必要としませんが、
// usePathname を使ってアクティブなリンクをハイライトする場合は必要になります。
// 今回はシンプルにするため、クライアントコンポーネントにはしません。

const navItems = [
  { name: "ランサムウェア攻撃", href: "/templates/ransomware", icon: KeyRound },
  { name: "ビジネスメール詐欺 (BEC)", href: "/templates/bec", icon: UserX },
  { name: "情報漏洩", href: "/templates/data-breach", icon: FileWarning },
];

export default function TemplatesLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="bg-white">
      <div className="container mx-auto px-4 py-12">
        <div className="flex flex-col md:flex-row gap-8 lg:gap-12">
          <aside className="md:w-1/4 lg:w-1/5">
            <h2 className="text-lg font-semibold mb-4 text-gray-800">文言集カテゴリ</h2>
            <nav className="flex flex-col space-y-2">
              {navItems.map((item) => (
                <Link
                  key={item.name}
                  href={item.href}
                  className="flex items-center gap-3 px-3 py-2 text-gray-600 hover:bg-gray-100 hover:text-gray-900 rounded-md transition-colors"
                >
                  <item.icon className="h-5 w-5" />
                  <span>{item.name}</span>
                </Link>
              ))}
            </nav>
          </aside>
          <main className="md:w-3/4 lg:w-4/5">
            {children}
          </main>
        </div>
      </div>
    </div>
  );
}
