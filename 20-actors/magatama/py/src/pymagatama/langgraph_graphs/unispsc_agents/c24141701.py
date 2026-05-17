from typing import TypedDict
from langgraph.graph import StateGraph, END

class CoreState(TypedDict):
    specs: dict
    validated: bool

def validate_specs(state: CoreState):
    required = ['inner_diameter_mm', 'length_mm']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

def check_crush(state: CoreState):
    if state.get('validated') and state['specs'].get('crush_strength_n', 0) < 500:
        print('Warning: Low crush strength detected')
    return state

graph = StateGraph(CoreState)
graph.add_node('validate', validate_specs)
graph.add_node('strength_check', check_crush)
graph.add_edge('validate', 'strength_check')
graph.add_edge('strength_check', END)
graph.set_entry_point('validate')
graph = graph.compile()