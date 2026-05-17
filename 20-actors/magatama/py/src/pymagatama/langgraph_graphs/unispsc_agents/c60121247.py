from typing import TypedDict
from langgraph.graph import StateGraph, END

class EaselState(TypedDict):
    specs: dict
    is_validated: bool

def validate_specs(state: EaselState):
    required = ['wood_type', 'max_canvas_height']
    state['is_validated'] = all(k in state['specs'] for k in required)
    return state

def check_quality(state: EaselState):
    print('Checking easel stability and wood finish...')
    return state

graph = StateGraph(EaselState)
graph.add_node('validate', validate_specs)
graph.add_node('quality_check', check_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'quality_check')
graph.add_edge('quality_check', END)
graph = graph.compile()