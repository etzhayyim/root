from typing import TypedDict
from langgraph.graph import StateGraph, END

class SVCState(TypedDict):
    voltage_rating: float
    mvar_capacity: float
    is_compliant: bool

def validate_specs(state: SVCState):
    state['is_compliant'] = state['voltage_rating'] >= 6.6 and state['mvar_capacity'] > 0
    return state

def check_compliance(state: SVCState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(SVCState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'compliant': END, 'non_compliant': END})
graph.compile()