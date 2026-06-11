import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Badge } from "@/components/ui/badge"

export function ScreeningDetailsTabs() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Screening Details</CardTitle>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="sanctions">
          <TabsList className="grid w-full grid-cols-3 md:grid-cols-6">
            <TabsTrigger value="sanctions">
              Sanctions{" "}
              <Badge variant="destructive" className="ml-2">
                1
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="pep">
              PEP{" "}
              <Badge variant="secondary" className="ml-2">
                2
              </Badge>
            </TabsTrigger>
            <TabsTrigger value="adverse_media">Adverse Media</TabsTrigger>
            <TabsTrigger value="ubo">UBO</TabsTrigger>
            <TabsTrigger value="crypto">Crypto</TabsTrigger>
            <TabsTrigger value="digital_id">Digital ID</TabsTrigger>
          </TabsList>
          <TabsContent value="sanctions" className="mt-4">
            <div className="p-4 border rounded-md bg-muted/50">
              <h4 className="font-semibold">OFAC Specially Designated Nationals List</h4>
              <p className="text-sm text-muted-foreground">Match Found: 98% confidence</p>
              <ul className="mt-2 list-disc pl-5 text-sm space-y-1">
                <li>
                  Name: <span className="font-mono">Jon Doe</span> (Matches <span className="font-mono">John Doe</span>)
                </li>
                <li>DOB: Not provided</li>
                <li>Nationality: Not provided</li>
                <li>Reason for listing: Suspected financial crimes.</li>
              </ul>
            </div>
          </TabsContent>
          <TabsContent value="pep" className="mt-4">
            <div className="space-y-4">
              <div className="p-4 border rounded-md bg-muted/50">
                <h4 className="font-semibold">Jane Doe (Spouse)</h4>
                <p className="text-sm text-muted-foreground">PEP Category 2: Family Member of a PEP</p>
                <ul className="mt-2 list-disc pl-5 text-sm">
                  <li>Position: Spouse of a former government official.</li>
                </ul>
              </div>
              <div className="p-4 border rounded-md bg-muted/50">
                <h4 className="font-semibold">Richard Roe (Business Associate)</h4>
                <p className="text-sm text-muted-foreground">PEP Category 3: Close Associate of a PEP</p>
                <ul className="mt-2 list-disc pl-5 text-sm">
                  <li>Relationship: Co-director of a company with a known PEP.</li>
                </ul>
              </div>
            </div>
          </TabsContent>
          {/* Add other TabsContent for adverse_media, ubo, etc. */}
        </Tabs>
      </CardContent>
    </Card>
  )
}
