from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_id: str
    validation_checks: List[str]
    approved: bool

def validate_biosafety(state: ProcurementState):
    # Simulate biosafety check logic
    state['validation_checks'].append('biosafety_verified')
    return state

def check_expiry(state: ProcurementState):
    state['validation_checks'].append('expiry_compliance_verified')
    state['approved'] = True
    return state

graph = StateGraph(ProcurementState)
graph.add_node('biosafety', validate_biosafety)
graph.add_node('expiry', check_expiry)
graph.set_entry_point('biosafety')
graph.add_edge('biosafety', 'expiry')
graph.add_edge('expiry', END)
app = graph.compile()