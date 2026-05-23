from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class AuditState(TypedDict):
    item_id: str
    compliance_docs: List[str]
    validated: bool

def validate_specs(state: AuditState):
    if "calibration_certification_document" in state['compliance_docs']:
        state['validated'] = True
    else:
        state['validated'] = False
    return state

graph = StateGraph(AuditState)
graph.add_node("validate", validate_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
