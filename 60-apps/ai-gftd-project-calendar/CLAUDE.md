# ai-gftd-project-calendar — Calendar Intelligence

> **T2 Logical Actor**: Manifest-driven (`20-actors/calendar/actor-manifest.jsonld`).

`calendar.etzhayyim.com` — iCalendar RFC 5545 互換 calendar event intelligence.

## Lexicons
`calendar/` (3 files): rsvp, createEvent, listEvents.

## Schema
- RFC 5545 RRULE for recurrence
- 3 visibility (public / private / confidential)
- attendeeDids 配列で多者 calendar 連携
- IANA timezone

## cross-actor
- `briefing` — meeting calendar sync
- `shinkansen` — reservation auto-add to calendar
- `gmail` / `outlook` — invitation flow
