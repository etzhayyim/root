"use client"

import { useState } from "react"
import { Button } from "@/ports/ui/components/ui/button"
import { Check, Copy } from "lucide-react"

interface CodeBlockProps {
  code: string
}

export function CodeBlock({ code }: CodeBlockProps) {
  const [hasCopied, setHasCopied] = useState(false)

  const copyToClipboard = () => {
    navigator.clipboard.writeText(code.trim())
    setHasCopied(true)
    setTimeout(() => setHasCopied(false), 2000)
  }

  return (
    <div className="relative">
      <pre className="bg-gray-800 text-white p-4 rounded-lg overflow-x-auto text-sm font-mono">
        <code>{code.trim()}</code>
      </pre>
      <Button
        size="icon"
        variant="ghost"
        className="absolute top-2 right-2 text-gray-400 hover:text-white hover:bg-gray-700"
        onClick={copyToClipboard}
      >
        {hasCopied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
        <span className="sr-only">Copy code</span>
      </Button>
    </div>
  )
}
