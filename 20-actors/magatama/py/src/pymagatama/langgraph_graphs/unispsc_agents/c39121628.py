from typing import TypedDict
from langgraph.graph import StateGraph, END

class FuseState(TypedDict):
    voltage_rating: float
    current_rating: float
    compliance_checked: bool
    validation_passed: bool

def validate_fuse_specs(state: FuseState):
    if state['voltage_rating'] > 0 and state['current_rating'] > 0:
        return {'validation_passed': True}
    return {'validation_passed': False}

def check_compliance(state: FuseState):
    return {'compliance_checked': True}

graph = StateGraph(FuseState)
graph.add_node('validate', validate_fuse_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()