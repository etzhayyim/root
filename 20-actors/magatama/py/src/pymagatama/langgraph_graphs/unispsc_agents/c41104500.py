from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class OvenSpecState(TypedDict):
    temp_range: str
    chamber_volume: float
    certification_docs: List[str]
    validation_score: float

def validate_specs(state: OvenSpecState):
    # Simulate CAD/spec validation logic
    state['validation_score'] = 1.0 if 'ISO-9001' in state['certification_docs'] else 0.5
    return state

def check_compliance(state: OvenSpecState):
    print(f"Validating oven specs. Score: {state['validation_score']}")
    return "end"

graph = StateGraph(OvenSpecState)
graph.add_node("validate", validate_specs)
graph.add_node("compliance", check_compliance)
graph.set_entry_point("validate")
graph.add_edge("validate", "compliance")
graph.add_edge("compliance", END)
graph = graph.compile()
