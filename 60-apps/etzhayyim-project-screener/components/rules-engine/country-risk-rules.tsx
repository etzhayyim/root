"use client"
import { useState } from "react"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { X } from "lucide-react"

export function CountryRiskRules() {
  const [countries, setCountries] = useState(["North Korea", "Iran", "Syria"])
  const [newCountry, setNewCountry] = useState("")

  const addCountry = () => {
    if (newCountry && !countries.includes(newCountry)) {
      setCountries([...countries, newCountry])
      setNewCountry("")
    }
  }

  const removeCountry = (countryToRemove: string) => {
    setCountries(countries.filter((c) => c !== countryToRemove))
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>High-Risk Countries</CardTitle>
        <CardDescription>Manage the list of countries that require enhanced due diligence.</CardDescription>
      </CardHeader>
      <CardContent>
        <div className="grid gap-4">
          <div className="grid gap-2">
            <Label htmlFor="add-country">Add Country</Label>
            <div className="flex gap-2">
              <Input
                id="add-country"
                value={newCountry}
                onChange={(e) => setNewCountry(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && addCountry()}
              />
              <Button onClick={addCountry}>Add</Button>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            {countries.map((country) => (
              <Badge key={country} variant="secondary" className="text-sm py-1 pl-3 pr-1">
                {country}
                <button onClick={() => removeCountry(country)} className="ml-2 rounded-full hover:bg-muted p-0.5">
                  <X className="h-3 w-3" />
                </button>
              </Badge>
            ))}
          </div>
        </div>
      </CardContent>
      <CardFooter className="border-t px-6 py-4">
        <Button>Save Changes</Button>
      </CardFooter>
    </Card>
  )
}
