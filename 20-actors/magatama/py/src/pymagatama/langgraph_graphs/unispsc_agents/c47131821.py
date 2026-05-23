from typing import TypedDict
from langgraph.graph import StateGraph, END

class DegreasingState(TypedDict):
    chemical_data: dict
    compliance_check: bool
    approved: bool

def validate_safety_data(state: DegreasingState):
    # Check flash point and VOC standards
    compliance = state['chemical_data'].get('flash_point', 0) > 60
    return {'compliance_check': compliance}

def approval_step(state: DegreasingState):
    return {'approved': state['compliance_check']}

graph = StateGraph(DegreasingState)
graph.add_node('validate', validate_safety_data)
graph.add_node('approve', approval_step)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
