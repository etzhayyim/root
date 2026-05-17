from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StampRackState(TypedDict):
    specifications: dict
    validation_errors: List[str]
    is_approved: bool

def validate_dimensions(state: StampRackState):
    specs = state.get('specifications', {})
    if 'dimensions' not in specs:
        state['validation_errors'].append('Missing dimensions')
    return state

def check_material_safety(state: StampRackState):
    if state.get('specifications', {}).get('material') == 'unknown':
        state['validation_errors'].append('Material safety check failed')
    return state

graph = StateGraph(StampRackState)
graph.add_node('validate_dims', validate_dimensions)
graph.add_node('check_material', check_material_safety)
graph.set_entry_point('validate_dims')
graph.add_edge('validate_dims', 'check_material')
graph.add_edge('check_material', END)

app = graph.compile()