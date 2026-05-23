from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PaintState(TypedDict):
    product_id: str
    voc_level: float
    flash_point: float
    compliance_passed: bool

def check_compliance(state: PaintState):
    # Validation logic for high VOC or low flash point oil-based paints
    passed = state['voc_level'] < 450 and state['flash_point'] > 30
    return {'compliance_passed': passed}

def route_by_compliance(state: PaintState):
    return "process" if state['compliance_passed'] else "reject"

graph = StateGraph(PaintState)
graph.add_node("validate", check_compliance)
graph.add_node("process", lambda x: print("Processing shipment"))
graph.add_node("reject", lambda x: print("Rejecting: Safety violation"))
graph.set_entry_point("validate")
graph.add_conditional_edges("validate", route_by_compliance)
graph.add_edge("process", END)
graph.add_edge("reject", END)
graph = graph.compile()
