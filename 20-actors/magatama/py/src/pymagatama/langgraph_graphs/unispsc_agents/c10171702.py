from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class FeedAdditiveState(TypedDict):
    additive_code: str
    quality_checks: Annotated[List[str], operator.add]
    is_approved: bool

def validate_composition(state: FeedAdditiveState):
    print(f"Validating composition for {state['additive_code']}")
    return {"quality_checks": ["composition_verified"], "is_approved": True}

def check_regulatory_compliance(state: FeedAdditiveState):
    print(f"Checking regulatory compliance for {state['additive_code']}")
    return {"quality_checks": ["regulations_met"], "is_approved": True}

graph = StateGraph(FeedAdditiveState)
graph.add_node("validate", validate_composition)
graph.add_node("comply", check_regulatory_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "comply")
graph.add_edge("comply", END)
graph = graph.compile()