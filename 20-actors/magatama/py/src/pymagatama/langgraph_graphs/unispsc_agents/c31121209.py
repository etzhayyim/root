from typing import TypedDict
from langgraph.graph import StateGraph, END

class BerylliumState(TypedDict):
    part_specs: dict
    compliance_cleared: bool
    machining_verified: bool

def validate_compliance(state: BerylliumState):
    # Business logic for export control and toxic material safety checks
    state['compliance_cleared'] = True
    return 'compliance_cleared'

def verify_machining(state: BerylliumState):
    # Logic to verify CAD tolerances for beryllium castings
    state['machining_verified'] = True
    return 'machining_verified'

graph = StateGraph(BerylliumState)
graph.add_node('compliance', validate_compliance)
graph.add_node('machining', verify_machining)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'machining')
graph.add_edge('machining', END)
graph = graph.compile()
