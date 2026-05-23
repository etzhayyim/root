from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SwimwearState(TypedDict):
    material: str
    uv_rating: str
    batch_id: str
    is_compliant: bool

def validate_specs(state: SwimwearState):
    state['is_compliant'] = state['uv_rating'] == 'UPF 50+' and 'polyester' in state['material'].lower()
    return state

def check_compliance(state: SwimwearState):
    return 'compliant_node' if state['is_compliant'] else 'reject_node'

graph = StateGraph(SwimwearState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'compliant_node': END, 'reject_node': END})
graph.compile()
