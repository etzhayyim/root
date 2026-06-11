# etzhayyim-project-emotional-analytics

`etzhayyim-project-emotional-analytics` provides standardized emotion signals for
conversation systems, including `etzhayyim-project-communicator`.

## Design scope

1. Analyze single message text and return normalized emotion vectors
2. Analyze thread windows and return trend signals
3. Recommend response style hints for downstream agents
4. Return explicit model/version metadata for auditability

## Signal model

1. `valence`: negative to positive direction
2. `arousal`: calm to activated intensity
3. `dominance`: passive to dominant stance
4. `urgency`: immediate action pressure
5. `confidence`: model confidence
6. `emotion_labels`: multi-label categorical outputs

## API contract

See: `proto/v1/emotional_analytics.proto`

## Integration notes for communicator

1. Communicator must pass tenant and conversation context metadata
2. Emotion outputs must be persisted with model version and timestamp
3. High urgency with negative valence should increase approval/risk thresholds
