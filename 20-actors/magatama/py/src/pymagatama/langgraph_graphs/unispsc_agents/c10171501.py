from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class FeedSupplementState(TypedDict):
    supplement_id: str
    quality_checks: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_composition(state: FeedSupplementState):
    # Simulated validation logic for animal feed supplements
    print(f"Validating composition for {state['supplement_id']}")
    return {"quality_checks": ["composition_verified"], "is_compliant": True}

def check_regulatory_status(state: FeedSupplementState):
    print(f"Checking regulatory compliance for {state['supplement_id']}")
    return {"quality_checks": ["regulatory_passed"]}

graph = StateGraph(FeedSupplementState)
graph.add_node("validate", validate_composition)
graph.add_node("regulate", check_regulatory_status)
graph.set_entry_point("validate")
graph.add_edge("validate", "regulate")
graph.add_edge("regulate", END)
app = graph.compile()