from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CatheterState(TypedDict):
    part_id: str
    compliance_docs: List[str]
    status: str

def validate_sterility(state: CatheterState):
    print(f"Validating sterility for {state['part_id']}")
    return {'status': 'validated' if 'ISO_13485' in state['compliance_docs'] else 'flagged'}

def process_procurement(state: CatheterState):
    print("Processing clinical procurement order")
    return {'status': 'ready_for_dispatch'}

graph = StateGraph(CatheterState)
graph.add_node("validate", validate_sterility)
graph.add_node("process", process_procurement)
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph.set_entry_point("validate")