import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Textarea } from "@/components/ui/textarea"
import { Button } from "@/components/ui/button"
import { Avatar, AvatarFallback } from "@/components/ui/avatar"

const trail = [
  { user: "Alex Ray", action: "Viewed customer profile", time: "5m ago", initials: "AR" },
  { user: "System", action: "Generated alert from Sanctions list match", time: "2h ago", initials: "S" },
]

export function AuditTrail() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Audit Trail & Notes</CardTitle>
        <CardDescription>History of actions and notes for this customer.</CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-4">
          {trail.map((item, index) => (
            <div key={index} className="flex items-start gap-3">
              <Avatar className="h-8 w-8">
                <AvatarFallback>{item.initials}</AvatarFallback>
              </Avatar>
              <div>
                <p className="text-sm font-medium">{item.user}</p>
                <p className="text-sm text-muted-foreground">
                  {item.action} - {item.time}
                </p>
              </div>
            </div>
          ))}
        </div>
        <div className="border-t pt-4">
          <Textarea placeholder="Add a note for your team..." />
          <Button className="mt-2 w-full">Add Note</Button>
        </div>
      </CardContent>
    </Card>
  )
}
