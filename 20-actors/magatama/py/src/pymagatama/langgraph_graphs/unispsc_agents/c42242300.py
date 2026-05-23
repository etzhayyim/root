from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OrthoState(TypedDict):
    item_id: str
    compliance_docs: List[str]
    is_approved: bool

def validate_compliance(state: OrthoState):
    # Simulate regulatory check logic for medical devices
    if 'ISO13485' in state['compliance_docs']:
        return {'is_approved': True}
    return {'is_approved': False}

def process_procurement(state: OrthoState):
    print(f"Processing orthopedic items: {state['item_id']}")
    return {}

graph = StateGraph(OrthoState)
graph.add_node("validate", validate_compliance)
graph.add_node("process", process_procurement)
graph.set_entry_point("validate")
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph_compiled = graph.compile()
