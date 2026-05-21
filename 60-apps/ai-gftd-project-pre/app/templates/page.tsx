import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { KeyRound, UserX, FileWarning, ArrowRight } from 'lucide-react';

export default function TemplatesHomePage() {
  return (
    <div>
      <h1 className="text-3xl font-bold mb-2 text-gray-900">広報文言集</h1>
      <p className="text-gray-600 mb-8">
        インシデントの種類を選択して、状況に応じたコミュニケーションテンプレートをご覧ください。
      </p>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3 mb-2">
              <KeyRound className="h-6 w-6 text-red-600" />
              <CardTitle>ランサムウェア攻撃</CardTitle>
            </div>
            <CardDescription>システム停止から復旧まで、各フェーズに応じたコミュニケーション文例集です。</CardDescription>
          </CardHeader>
          <div className="p-6 pt-0">
            <Link href="/templates/ransomware" className="text-primary font-semibold hover:underline flex items-center">
              詳細を見る <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </div>
        </Card>
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3 mb-2">
              <UserX className="h-6 w-6 text-yellow-600" />
              <CardTitle>ビジネスメール詐欺 (BEC)</CardTitle>
            </div>
            <CardDescription>取引先や社内への注意喚起、被害発生時の報告など、信頼を維持するための文例集です。</CardDescription>
          </CardHeader>
          <div className="p-6 pt-0">
            <Link href="/templates/bec" className="text-primary font-semibold hover:underline flex items-center">
              詳細を見る <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </div>
        </Card>
        <Card>
          <CardHeader>
            <div className="flex items-center gap-3 mb-2">
              <FileWarning className="h-6 w-6 text-blue-600" />
              <CardTitle>情報漏洩</CardTitle>
            </div>
            <CardDescription>規制当局への報告から顧客へのお詫びまで、誠実な対応を示すための文例集です。</CardDescription>
          </CardHeader>
          <div className="p-6 pt-0">
            <Link href="/templates/data-breach" className="text-primary font-semibold hover:underline flex items-center">
              詳細を見る <ArrowRight className="ml-1 h-4 w-4" />
            </Link>
          </div>
        </Card>
      </div>
    </div>
  );
}
