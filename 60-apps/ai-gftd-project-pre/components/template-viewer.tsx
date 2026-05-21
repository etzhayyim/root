'use client';

import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Check, Copy } from 'lucide-react';

interface TemplateViewerProps {
  title: string;
  description: string;
  content: string;
}

export default function TemplateViewer({ title, description, content }: TemplateViewerProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(content.trim());
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <Card className="mb-8">
      <CardHeader className="flex flex-row items-center justify-between">
        <div>
          <CardTitle className="text-xl">{title}</CardTitle>
          <p className="text-sm text-gray-500 mt-1">{description}</p>
        </div>
        <Button variant="outline" size="icon" onClick={handleCopy}>
          {copied ? <Check className="h-4 w-4 text-green-500" /> : <Copy className="h-4 w-4" />}
          <span className="sr-only">コピー</span>
        </Button>
      </CardHeader>
      <CardContent>
        <pre className="bg-gray-50 p-4 rounded-md text-sm whitespace-pre-wrap font-sans overflow-x-auto">
          <code>{content.trim()}</code>
        </pre>
      </CardContent>
    </Card>
  );
}
