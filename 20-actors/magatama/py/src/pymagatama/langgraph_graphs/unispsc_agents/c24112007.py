from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RackState(TypedDict):
    load_capacity: float
    specs: dict
    is_compliant: bool

def validate_specs(state: RackState):
    limit = state['specs'].get('load_capacity_kg', 0)
    state['is_compliant'] = limit > 0 and limit <= 5000
    return state

def check_compliance(state: RackState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(RackState)
graph.add_node('validate', validate_specs)
graph.add_conditional_edges('validate', check_compliance, {'compliant': END, 'non_compliant': END})
graph.set_entry_point('validate')
graph = graph.compile()
