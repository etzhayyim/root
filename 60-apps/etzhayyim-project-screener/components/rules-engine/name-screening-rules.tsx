"use client"
import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Slider } from "@/components/ui/slider"
import { Button } from "@/components/ui/button"

export function NameScreeningRules() {
  const [confidence, setConfidence] = useState([85])

  return (
    <Card>
      <CardHeader>
        <CardTitle>Name Screening</CardTitle>
        <CardDescription>Define the fuzzy matching confidence score for creating alerts.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="confidence-slider">Alert Threshold</Label>
            <div className="flex items-center gap-4">
              <Slider
                id="confidence-slider"
                min={50}
                max={100}
                step={1}
                value={confidence}
                onValueChange={setConfidence}
              />
              <span className="font-semibold w-12 text-right">{confidence[0]}%</span>
            </div>
            <p className="text-xs text-muted-foreground">
              Name matches with a confidence score above this value will generate a high-priority alert.
            </p>
          </div>
        </div>
      </CardContent>
      <CardFooter className="border-t px-6 py-4">
        <Button>Save Changes</Button>
      </CardFooter>
    </Card>
  )
}
