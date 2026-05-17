from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    regulatory_compliant: bool
    permits_verified: bool

def check_compliance(state: ProcurementState):
    # Simulated compliance logic for controlled substances
    state['regulatory_compliant'] = True
    return 'check_permits'

def check_permits(state: ProcurementState):
    state['permits_verified'] = True
    return END

graph = StateGraph(ProcurementState)
graph.add_node('compliance', check_compliance)
graph.add_node('check_permits', check_permits)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'check_permits')
graph.add_edge('check_permits', END)
graph = graph.compile()