from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    temp_log: List[float]
    audit_passed: bool

def validate_cold_chain(state: ProcurementState):
    # Ensure temperature did not exceed -18C
    state['audit_passed'] = all(t <= -18.0 for t in state['temp_log'])
    return state

def check_certification(state: ProcurementState):
    # Dummy logic for cert verification
    return {'audit_passed': state['audit_passed'] and True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()