from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlangeState(TypedDict):
    part_id: str
    specs: dict
    is_compliant: bool

def validate_specs(state: FlangeState):
    required = ['material', 'outer_diameter']
    state['is_compliant'] = all(k in state['specs'] for k in required)
    return state

def check_dimensions(state: FlangeState):
    if state['is_compliant']:
        print(f'Validating flange dimensions for {state['part_id']}')
    return state

graph_builder = StateGraph(FlangeState)
graph_builder.add_node('validate', validate_specs)
graph_builder.add_node('dimensions', check_dimensions)
graph_builder.add_edge('validate', 'dimensions')
graph_builder.add_edge('dimensions', END)
graph_builder.set_entry_point('validate')
graph = graph_builder.compile()
