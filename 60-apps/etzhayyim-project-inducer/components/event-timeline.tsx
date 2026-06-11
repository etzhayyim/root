import { Bot, Mail, MousePointerClick, Search, User } from "lucide-react"

export default function EventTimeline() {
  const events = [
    { icon: User, color: "text-sky-500", text: "Contact added to system from CRM.", time: "2 days ago" },
    { icon: Search, color: "text-slate-500", text: "Visited pricing page for 3 minutes.", time: "1 day ago" },
    {
      icon: Bot,
      color: "text-purple-500",
      text: "Intent Engine detected 'High Interest in Pricing'.",
      time: "1 day ago",
    },
    {
      icon: Mail,
      color: "text-amber-500",
      text: "Email Agent sent 'Pricing Follow-up' sequence.",
      time: "23 hours ago",
    },
    {
      icon: MousePointerClick,
      color: "text-green-500",
      text: "Clicked link 'Book a Demo' in email.",
      time: "15 hours ago",
    },
    { icon: Bot, color: "text-purple-500", text: "Response Analyzer flagged for human review.", time: "15 hours ago" },
    {
      icon: User,
      color: "text-red-500",
      text: "Assigned to Sales Rep 'John Doe' for manual follow-up.",
      time: "14 hours ago",
    },
  ]

  return (
    <div className="relative pl-8">
      <div className="absolute left-4 top-0 h-full w-0.5 bg-muted" />
      {events.map((event, index) => (
        <div key={index} className="relative mb-8 flex items-start">
          <div className="absolute -left-0.5 top-1.5 flex h-9 w-9 items-center justify-center rounded-full bg-background">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-muted">
              <event.icon className={`h-5 w-5 ${event.color}`} />
            </div>
          </div>
          <div className="ml-4">
            <p className="font-medium text-foreground">{event.text}</p>
            <p className="text-sm text-muted-foreground">{event.time}</p>
          </div>
        </div>
      ))}
    </div>
  )
}
