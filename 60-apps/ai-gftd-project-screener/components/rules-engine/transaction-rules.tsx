"use client"
import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { useToast } from "@/components/ui/use-toast"

export function TransactionRules() {
  const { toast } = useToast()
  const [threshold, setThreshold] = useState("10000")
  const [isLoading, setIsLoading] = useState(false)

  const handleSave = async () => {
    setIsLoading(true)
    try {
      throw new Error(
        "Unsupported transport: direct runtime HTTP calls are disabled and no local Connect client/descriptor mapping exists."
      )
    } catch (error) {
      toast({
        title: "Update Failed",
        description: error instanceof Error ? error.message : "Could not publish the rule change event.",
        variant: "destructive",
      })
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Transaction Monitoring</CardTitle>
        <CardDescription>Set thresholds for flagging suspicious transactions.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="tx-threshold">Single Transaction Threshold (USD)</Label>
            <Input id="tx-threshold" type="number" value={threshold} onChange={(e) => setThreshold(e.target.value)} />
            <p className="text-xs text-muted-foreground">
              Transactions exceeding this amount will be automatically flagged.
            </p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="border-t px-6 py-4">
        <Button onClick={handleSave} disabled={isLoading}>
          {isLoading ? "Saving..." : "Save Changes"}
        </Button>
      </CardFooter>
    </Card>
  )
}
