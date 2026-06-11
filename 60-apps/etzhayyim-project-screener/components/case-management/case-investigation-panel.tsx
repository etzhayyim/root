import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const notes = [
  {
    user: "Alex Ray",
    text: "Initial review of sanctions match. Confidence is high. Proceeding with EDD.",
    time: "1h ago",
    initials: "AR",
  },
  { user: "System", text: "Case created from alert on customer CUST-001.", time: "2h ago", initials: "S" },
]

export function CaseInvestigationPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Investigation Workspace</CardTitle>
        <CardDescription>Document findings and resolve the case.</CardDescription>
      </CardHeader>
      <CardContent>
        <Tabs defaultValue="notes">
          <TabsList className="grid w-full grid-cols-2">
            <TabsTrigger value="notes">Investigation Notes</TabsTrigger>
            <TabsTrigger value="resolution">Close Case</TabsTrigger>
          </TabsList>
          <TabsContent value="notes" className="mt-4">
            <div className="space-y-4">
              <Textarea placeholder="Add an investigation note..." className="min-h-[100px]" />
              <Button>Add Note</Button>
              <div className="border-t pt-4 space-y-6">
                {notes.map((note, index) => (
                  <div key={index} className="flex items-start gap-4">
                    <Avatar className="h-9 w-9">
                      <AvatarFallback>{note.initials}</AvatarFallback>
                    </Avatar>
                    <div className="w-full">
                      <div className="flex items-center justify-between">
                        <p className="text-sm font-medium">{note.user}</p>
                        <p className="text-xs text-muted-foreground">{note.time}</p>
                      </div>
                      <p className="text-sm mt-1 bg-muted p-3 rounded-md">{note.text}</p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>
          <TabsContent value="resolution" className="mt-4">
            <div className="space-y-4 p-4 border rounded-lg">
              <h4 className="font-semibold">Case Resolution</h4>
              <div className="grid gap-2">
                <label htmlFor="resolution-reason" className="text-sm font-medium">
                  Reason for Closing
                </label>
                <Select>
                  <SelectTrigger id="resolution-reason">
                    <SelectValue placeholder="Select a reason" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="false-positive">False Positive</SelectItem>
                    <SelectItem value="confirmed-risk">Confirmed Risk - Action Taken</SelectItem>
                    <SelectItem value="insufficient-data">Insufficient Data</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="grid gap-2">
                <label htmlFor="final-comments" className="text-sm font-medium">
                  Final Comments
                </label>
                <Textarea id="final-comments" placeholder="Summarize the final outcome..." />
              </div>
              <Button className="w-full">Confirm and Close Case</Button>
            </div>
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  )
}
