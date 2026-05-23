from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MaterialState(TypedDict):
    material_id: str
    purity: float
    safety_clearance: bool
    log_steps: List[str]

def validate_material(state: MaterialState) -> MaterialState:
    if state['purity'] >= 99.9:
        state['safety_clearance'] = True
        state['log_steps'].append('Purity validation passed')
    else:
        state['safety_clearance'] = False
        state['log_steps'].append('Purity validation failed')
    return state

def route_by_clearance(state: MaterialState) -> str:
    return 'process' if state['safety_clearance'] else 'reject'

graph = StateGraph(MaterialState)
graph.add_node('validate', validate_material)
graph.add_node('process', lambda s: s)
graph.add_node('reject', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_clearance)
graph.add_edge('process', END)
graph.add_edge('reject', END)
graph = graph.compile()
