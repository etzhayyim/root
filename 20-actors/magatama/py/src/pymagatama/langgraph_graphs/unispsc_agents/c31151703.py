from typing import TypedDict
from langgraph.graph import StateGraph, END

class LiftingCableState(TypedDict):
    load_capacity: float
    safety_factor: float
    certification: str
    is_compliant: bool

def validate_specs(state: LiftingCableState):
    state['is_compliant'] = state['safety_factor'] >= 5.0 and state['load_capacity'] > 0
    return state

def check_compliance(state: LiftingCableState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(LiftingCableState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'compliant': END, 'non_compliant': END})
graph.compile()
