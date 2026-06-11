import { Avatar, AvatarImage, AvatarFallback } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Mail, MessageSquare } from "lucide-react"
import ContactActivityGraph from "@/components/contact-activity-graph"
import EventTimeline from "@/components/event-timeline"

export default function ContactDetailPage({ params }: { params: { id: string } }) {
  const contact = {
    id: params.id,
    name: "Alice Johnson",
    email: "alice@example.com",
    title: "Product Manager",
    company: "Innovate Inc.",
    tags: ["High-Value", "Tech", "Early Adopter"],
    engagementScore: 85,
  }

  return (
    <div className="flex min-h-screen w-full flex-col bg-muted/40">
      <main className="flex-1 space-y-4 p-4 md:space-y-8 md:p-8">
        <div className="flex items-center gap-4">
          <Avatar className="h-16 w-16">
            <AvatarImage src={`https://avatar.vercel.sh/${contact.email}.png`} />
            <AvatarFallback>{contact.name.charAt(0)}</AvatarFallback>
          </Avatar>
          <div>
            <h1 className="text-2xl font-bold">{contact.name}</h1>
            <p className="text-muted-foreground">
              {contact.title} at {contact.company}
            </p>
            <div className="flex flex-wrap gap-2 mt-2">
              {contact.tags.map((tag) => (
                <Badge key={tag}>{tag}</Badge>
              ))}
            </div>
          </div>
          <div className="ml-auto flex gap-2">
            <Button variant="outline">
              <Mail className="mr-2 h-4 w-4" />
              Send Email
            </Button>
            <Button>
              <MessageSquare className="mr-2 h-4 w-4" />
              Create Task
            </Button>
          </div>
        </div>

        <Tabs defaultValue="timeline">
          <TabsList>
            <TabsTrigger value="timeline">Actor-Network Timeline</TabsTrigger>
            <TabsTrigger value="graph">Activity Graph</TabsTrigger>
            <TabsTrigger value="profile">Profile Details</TabsTrigger>
          </TabsList>
          <TabsContent value="timeline">
            <Card>
              <CardHeader>
                <CardTitle>Actor-Network Timeline</CardTitle>
                <CardDescription>
                  A chronological view of all interactions between the contact and various agents (human and AI).
                </CardDescription>
              </CardHeader>
              <CardContent>
                <EventTimeline />
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="graph">
            <Card>
              <CardHeader>
                <CardTitle>Engagement Over Time</CardTitle>
                <CardDescription>
                  Visual representation of contact's engagement score based on their activities.
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ContactActivityGraph />
              </CardContent>
            </Card>
          </TabsContent>
          <TabsContent value="profile">
            <Card>
              <CardHeader>
                <CardTitle>Contact Profile</CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <p>
                  <strong>Email:</strong> {contact.email}
                </p>
                <p>
                  <strong>Company:</strong> {contact.company}
                </p>
                <p>
                  <strong>Title:</strong> {contact.title}
                </p>
                <p>
                  <strong>Engagement Score:</strong> {contact.engagementScore}
                </p>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  )
}
