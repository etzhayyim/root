import Link from "next/link";
import { Card, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { KeyRound, UserX, FileWarning, ArrowRight } from 'lucide-react';

export default function TemplatesSection() {
  return (
    <section id="templates" className="w-full bg-gray-50 py-16 md:py-24">
      <div className="container mx-auto px-4">
        <div className="text-center mb-12">
          <h2 className="text-3xl md:text-4xl font-bold">実践的なインシデント別 広報文言集</h2>
          <p className="mt-4 max-w-3xl mx-auto text-gray-600">
            CrisisComms Proには、あらゆる状況に対応するためのテンプレートが網羅されています。
            ここでは代表的な3つのシナリオの文例をご紹介します。
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <KeyRound className="h-8 w-8 text-red-600" />
                <CardTitle>ランサムウェア攻撃</CardTitle>
              </div>
              <CardDescription>システム停止から復旧まで、各フェーズに応じたコミュニケーション文例集です。</CardDescription>
            </CardHeader>
            <div className="p-6 pt-0">
              <Link href="/templates/ransomware">
                <Button className="w-full">
                  文例を見る <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <UserX className="h-8 w-8 text-yellow-600" />
                <CardTitle>ビジネスメール詐欺</CardTitle>
              </div>
              <CardDescription>取引先や社内への注意喚起、被害発生時の報告など、信頼を維持するための文例集です。</CardDescription>
            </CardHeader>
            <div className="p-6 pt-0">
              <Link href="/templates/bec">
                <Button className="w-full">
                  文例を見る <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </Card>

          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-center gap-3 mb-2">
                <FileWarning className="h-8 w-8 text-blue-600" />
                <CardTitle>情報漏洩</CardTitle>
              </div>
              <CardDescription>規制当局への報告から顧客へのお詫びまで、誠実な対応を示すための文例集です。</CardDescription>
            </CardHeader>
            <div className="p-6 pt-0">
              <Link href="/templates/data-breach">
                <Button className="w-full">
                  文例を見る <ArrowRight className="ml-2 h-4 w-4" />
                </Button>
              </Link>
            </div>
          </Card>
        </div>
      </div>
    </section>
  );
}
