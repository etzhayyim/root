import Link from "next/link";
import Image from "next/image";
import { Button } from "@/components/ui/button";

export default function Header() {
  return (
    <header className="w-full bg-white border-b border-gray-200">
      <div className="container mx-auto px-4 h-20 flex items-center justify-between">
        <Link href="/" className="flex items-center">
          <Image
            src="/logo.png"
            alt="etzhayyim PRE Logo"
            width={140}
            height={40}
            priority
          />
        </Link>
        <nav className="hidden md:flex items-center gap-6">
          <Link href="/" className="text-sm font-medium text-gray-600 hover:text-gray-900">
            ホーム
          </Link>
          <Link href="/templates" className="text-sm font-medium text-gray-600 hover:text-gray-900">
            文言集
          </Link>
        </nav>
        <Button asChild>
          <Link href="https://share.hsforms.com/1ktcvOuQyQryU6Qy98nvaRwp49om" target="_blank">
            事前お申し込み
          </Link>
        </Button>
      </div>
    </header>
  );
}
