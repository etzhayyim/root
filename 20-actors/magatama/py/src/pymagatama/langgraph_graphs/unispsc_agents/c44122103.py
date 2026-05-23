from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ClaspState(TypedDict):
    material: str
    capacity: float
    compliance_tags: List[str]
    approved: bool

def validate_specs(state: ClaspState):
    state['approved'] = state['capacity'] > 0 and 'RoHS' in state['compliance_tags']
    return state

def route_by_material(state: ClaspState):
    return 'process_metal' if state['material'] == 'metal' else 'process_plastic'

graph = StateGraph(ClaspState)
graph.add_node('validate', validate_specs)
graph.add_node('process_metal', lambda x: x)
graph.add_node('process_plastic', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_material)
graph.add_edge('process_metal', END)
graph.add_edge('process_plastic', END)
graph = graph.compile()
