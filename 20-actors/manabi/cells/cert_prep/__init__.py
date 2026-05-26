"""manabi.cert_prep — IT audit / infosec knowledge-domain study sub-cell.

Per ADR-2605264400 (sub-charter under ADR-2605261045 manabi master).

R0 scaffold. All four cells raise RuntimeError on activation until:
  1. ADR-2605264400 Council Lv6+ ≥3 ratify
  2. judah LiteLLM gateway operational with baien-server-moemoekyun-* fleet entry
  3. Initial CBK domain outline library (CISA D1-D5 + CISSP D1-D8) Council-reviewed
     for G4 charter alignment (manabi master) + G15-G17 (this sub-charter)
  4. Encrypted envelope (ADR-2605181100) production-deployed for adult session
     history persistence

Cells:
  - domain_review        — CISA/CISSP CBK domain concept reading
  - practice_question    — baien-moemoekyun synthetic question generation
  - self_assessment      — self-paced demonstration (G10 — untimed default)
  - personal_material    — Tier-C internal_only user-imported material (R2+)

Constitutional invariants beyond manabi master G1-G14:
  G15 — no pass-rate KPI (silenEducationReview cert_prep section schema-rejects pass-rate fields)
  G16 — no official past-question reproduction (questionSource closed enum)
  G17 — no external credential body partnership (ISACA/(ISC)²/CompTIA/EC-Council/SANS/Offensive Security)

Additional non-goals N11..N13:
  N11 — pass guarantee / pass-rate prediction
  N12 — formal partnership with any commercial credentialing body
  N13 — using cert_prep completion as employment gate within religious-corp roles
"""

from .domain_review import DomainReviewCell
from .practice_question import PracticeQuestionCell
from .self_assessment import SelfAssessmentCell
from .personal_material import PersonalMaterialCell

__all__ = [
    "DomainReviewCell",
    "PracticeQuestionCell",
    "SelfAssessmentCell",
    "PersonalMaterialCell",
]
