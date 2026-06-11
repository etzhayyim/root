# ninso.etzhayyim.com

人相 (Physiognomy) analysis — classifying personality, age, profile, fashion style from face photos and clothing. Statistics-first cohort assignment, no raw biometrics stored.

## Architecture

- **Ingest**: Follow photos.etzhayyim.com → on `com.etzhayyim.apps.photos.photo` create → analyze
- **Face Analysis**: Murakumo VL (qwen3-vl-8b) for apparent age, gender, facial structure, skin condition, expression
- **Personality Inference**: Big Five traits (openness, conscientiousness, extraversion, agreeableness, neuroticism) from facial features + clothing style
- **Fashion Classification**: clothing style, color palette, silhouette, era/trend via Murakumo VL
- **Cohort**: Analysis results → cohort hash → path-based DID assignment
- **Write**: Analysis records → PDS (Design E T2 Domain write)
- **Social**: Profile summaries → T1 Social write
- **Cross-reference**: photos (blob source), natural-person (demographics), joucho (emotional scoring), society6 (Kyu/Dan)

## Murakumo Model Stack

| Layer | Model | Use | Routing |
|---|---|---|---|
| Face analysis | qwen3-vl-8b | Age, gender, structure, skin, expression | MLX → Workers AI |
| Personality inference | qwen3-vl-8b | Big Five from face+clothing composite | MLX → Workers AI |
| Fashion classification | qwen3-vl-8b | Style, palette, silhouette, era | MLX → Workers AI |

## Multi-DID Architecture

| DID Pattern | Purpose |
|---|---|
| `did:web:ninso.etzhayyim.com` | Primary controller |
| `did:web:ninso.etzhayyim.com:face:{cohort_hash}` | Face analysis cohort |
| `did:web:ninso.etzhayyim.com:style:{cohort_hash}` | Fashion/style cohort |
| `did:web:ninso.etzhayyim.com:profile:{cohort_hash}` | Combined profile cohort |

## Face Cohort Dimensions (14)

| Dim | Type | Values |
|---|---|---|
| `country` | string | ISO 3166-1 alpha-2 |
| `age_class` | enum | child, youth, young_adult, adult, middle_aged, elderly |
| `gender_apparent` | enum | male, female, unknown |
| `face_shape` | enum | oval, round, square, heart, oblong, diamond, unknown |
| `skin_condition` | enum | clear, acne, wrinkled, freckled, tanned, fair, unknown |
| `expression` | enum | neutral, happy, sad, angry, surprised, disgusted, fearful, contempt, unknown |
| `big5_openness` | enum | low, medium, high |
| `big5_conscientiousness` | enum | low, medium, high |
| `big5_extraversion` | enum | low, medium, high |
| `big5_agreeableness` | enum | low, medium, high |
| `big5_neuroticism` | enum | low, medium, high |
| `glasses` | enum | none, glasses, sunglasses |
| `facial_hair` | enum | none, mustache, beard, goatee, stubble, unknown |
| `time_slot` | enum | dawn, morning, afternoon, evening, night |

Cohort hash: DJB2 over `|`-joined canonical string → `"f" + hex(h) + hex(len)` (13 chars, alpha-start).

## Style Cohort Dimensions (10)

| Dim | Type | Values |
|---|---|---|
| `clothing_style` | enum | casual, formal, business, streetwear, traditional, athletic, bohemian, minimalist, vintage, punk, gothic, preppy, unknown |
| `color_palette` | enum | monochrome, warm, cool, neutral, pastel, vivid, dark, earth, unknown |
| `silhouette` | enum | fitted, relaxed, oversized, layered, structured, flowing, unknown |
| `era_trend` | enum | classic, contemporary, retro_70s, retro_80s, retro_90s, y2k, futuristic, unknown |
| `formality_level` | enum | very_casual, casual, smart_casual, business_casual, formal, black_tie, unknown |
| `season_suitability` | enum | spring, summer, autumn, winter, all_season, unknown |
| `upper_color` | option | color slug |
| `lower_color` | option | color slug |
| `accessory` | enum | hat, scarf, jewelry, watch, bag, none, unknown |
| `gender_style` | enum | masculine, feminine, androgynous, unknown |

Cohort hash: DJB2 → `"s" + hex(h) + hex(len)` (13 chars, alpha-start).

## Profile Cohort Dimensions (8)

| Dim | Type | Values |
|---|---|---|
| `age_class` | enum | (from face) |
| `gender_apparent` | enum | (from face) |
| `dominant_big5` | enum | openness, conscientiousness, extraversion, agreeableness, neuroticism |
| `clothing_style` | enum | (from style) |
| `formality_level` | enum | (from style) |
| `color_palette` | enum | (from style) |
| `impression` | enum | professional, creative, casual, authoritative, approachable, mysterious, energetic, serene, unknown |
| `natural_person_cohort_hash` | option | Link to natural-person.etzhayyim.com |

Cohort hash: DJB2 → `"n" + hex(h) + hex(len)` (13 chars, alpha-start).

Cross-link: `MATCH (nc:NinsoProfileCohort)-[:MAPS_TO]->(np:NaturalPersonCohort)` via shared dimension overlap.

## W Protocol Lexicon (NSID)

| NSID | Type | Description |
|---|---|---|
| `com.etzhayyim.apps.ninso.faceAnalysis` | record | Face analysis result (derived classifications) |
| `com.etzhayyim.apps.ninso.personalityInference` | record | Big Five personality inference |
| `com.etzhayyim.apps.ninso.styleClassification` | record | Fashion/style classification |
| `com.etzhayyim.apps.ninso.profile` | record | Combined profile (face + personality + style) |
| `com.etzhayyim.apps.ninso.faceCohort` | record | Face cohort statistics |
| `com.etzhayyim.apps.ninso.styleCohort` | record | Style cohort statistics |
| `com.etzhayyim.apps.ninso.profileCohort` | record | Combined profile cohort statistics |
| `com.etzhayyim.apps.ninso.analysisJob` | record | Analysis job tracking |

## SQL Graph Schema

```sql
(:NinsoFaceAnalysis {id, photoRef, ageClass, genderApparent, faceShape, skinCondition, expression, glasses, facialHair, confidence, modelVersion, createdAt})
(:NinsoPersonalityInference {id, photoRef, openness, conscientiousness, extraversion, agreeableness, neuroticism, dominantTrait, confidence, modelVersion, createdAt})
(:NinsoStyleClassification {id, photoRef, clothingStyle, colorPalette, silhouette, eraTrend, formalityLevel, seasonSuitability, upperColor, lowerColor, accessory, genderStyle, confidence, modelVersion, createdAt})
(:NinsoProfile {id, photoRef, faceAnalysisId, personalityId, styleId, impression, profileCohortHash, createdAt})
(:NinsoFaceCohort {cohortHash, did, dimensionsJson, count, firstSeen, lastSeen})
(:NinsoStyleCohort {cohortHash, did, dimensionsJson, count, firstSeen, lastSeen})
(:NinsoProfileCohort {cohortHash, did, dimensionsJson, count, firstSeen, lastSeen})
(:NinsoAnalysisJob {id, photoRef, status, phase, createdAt, completedAt})

(:NinsoFaceAnalysis)-[:FROM_PHOTO]->(:Photo)
(:NinsoPersonalityInference)-[:FROM_FACE]->(:NinsoFaceAnalysis)
(:NinsoStyleClassification)-[:FROM_PHOTO]->(:Photo)
(:NinsoProfile)-[:HAS_FACE]->(:NinsoFaceAnalysis)
(:NinsoProfile)-[:HAS_PERSONALITY]->(:NinsoPersonalityInference)
(:NinsoProfile)-[:HAS_STYLE]->(:NinsoStyleClassification)
(:NinsoProfile)-[:IN_COHORT]->(:NinsoProfileCohort)
(:NinsoFaceCohort)-[:MAPS_TO]->(:NaturalPersonCohort)
(:NinsoProfileCohort)-[:MAPS_TO]->(:NaturalPersonCohort)
```

## Privacy

- No raw facial biometrics stored — only derived categorical classifications
- No face recognition — no embedding vectors, no re-identification
- Statistics-first: cohort = statistical aggregate, not individual identification
- Photo ref only: ninso stores blob URI from photos.etzhayyim.com, not image data
- Governance: `classification: restricted`, GDPR Art.9, APPI
- Consent: analysis only on photos explicitly submitted to ninso pipeline
- Personality disclaimer: "Statistical inference only. Not a psychological assessment."
- Retention: analysis records 90d, cohort records indefinite, analysis_job 7d
