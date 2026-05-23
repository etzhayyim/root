from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    materials: List[str]
    validation_report: str
    approved: bool

def validate_content(state: ProcurementState):
    report = f"Validating materials: {', '.join(state['materials'])} for educational compliance."
    return {'validation_report': report, 'approved': True}

def finalize_order(state: ProcurementState):
    return {'validation_report': state['validation_report'] + " - Order finalized."}

graph = StateGraph(ProcurementState)
graph.add_node("validate", validate_content)
graph.add_node("finalize", finalize_order)
graph.set_entry_point("validate")
graph.add_edge("validate", "finalize")
graph.add_edge("finalize", END)
app = graph.compile()
