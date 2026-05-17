# livecam-vision-actor

LangServer worker for `livecam.gftd.ai` camera-frame analysis.

Responsibilities:
- fetch camera frame images when only `imageUrl` is supplied
- call Murakumo/OpenAI-compatible vision models
- parse structured person/vehicle detections
- assemble cohort and detection-event records
- call `ai.gftd.apps.livecam.commitAnalysis` on the edge worker

The Cloudflare/appview worker remains the thin edge boundary for PDS writes and social posting.
