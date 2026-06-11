import Link from "next/link";
import Image from "next/image";

export default function Footer() {
  return (
    <footer className="w-full bg-gray-100 border-t border-gray-200">
      <div className="container mx-auto px-4 py-8">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div className="flex flex-col items-center md:items-start">
            <Link href="/" className="mb-2">
              <Image
                src="/logo.png"
                alt="etzhayyim PRE Logo"
                width={120}
                height={34}
              />
            </Link>
            <p className="text-sm text-gray-500">
              サイバー危機を、信頼回復の機会に変える。
            </p>
          </div>
          <p className="text-sm text-gray-500">
            &copy; {new Date().getFullYear()} etzhayyim PRE. All Rights Reserved.
          </p>
        </div>
      </div>
    </footer>
  );
}
