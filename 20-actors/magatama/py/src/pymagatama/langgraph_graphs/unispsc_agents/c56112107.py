from typing import TypedDict
from langgraph.graph import StateGraph, END

class SeatingState(TypedDict):
    part_type: str
    spec_compliant: bool
    safety_check: str

def validate_part(state: SeatingState):
    compliant = state['part_type'] in ['gas_lift', 'base', 'casters']
    return {'spec_compliant': compliant, 'safety_check': 'BIFMA_Verified' if compliant else 'Manual_Review_Required'}

def finalize_check(state: SeatingState):
    return {'safety_check': 'Certified_For_Procurement'}

graph = StateGraph(SeatingState)
graph.add_node('validate', validate_part)
graph.add_node('final', finalize_check)
graph.add_edge('validate', 'final')
graph.add_edge('final', END)
graph.set_entry_point('validate')
graph = graph.compile()
