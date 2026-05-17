from typing import TypedDict
from langgraph.graph import StateGraph, END

class MarkerState(TypedDict):
    part_number: str
    spec_check: bool
    compliance_report: str

def validate_specs(state: MarkerState):
    # Simulate validation logic for cable diameter compliance
    return {"spec_check": True, "compliance_report": "Specifications verified against ANSI/TIA standards"}

def generate_label(state: MarkerState):
    return {"compliance_report": f"Label configured for part {state['part_number']}"}

graph = StateGraph(MarkerState)
graph.add_node("validate", validate_specs)
graph.add_node("format", generate_label)
graph.add_edge("validate", "format")
graph.add_edge("format", END)
graph.set_entry_point("validate")