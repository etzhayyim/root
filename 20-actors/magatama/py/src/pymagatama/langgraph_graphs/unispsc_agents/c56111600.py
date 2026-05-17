from typing import TypedDict
from langgraph.graph import StateGraph, END

class PanelState(TypedDict):
    spec_data: dict
    validated: bool

def validate_specs(state: PanelState):
    required = ['fire_rating', 'dimensions']
    all_found = all(k in state['spec_data'] for k in required)
    return {'validated': all_found}

def process_layout(state: PanelState):
    print('Processing panel layout configuration...')
    return {}

graph = StateGraph(PanelState)
graph.add_node('validate', validate_specs)
graph.add_node('layout', process_layout)
graph.set_entry_point('validate')
graph.add_edge('validate', 'layout')
graph.add_edge('layout', END)
graph = graph.compile()