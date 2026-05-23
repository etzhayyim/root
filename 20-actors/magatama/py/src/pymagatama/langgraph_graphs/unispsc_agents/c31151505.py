from typing import TypedDict
from langgraph.graph import StateGraph, END

class WireRopeState(TypedDict):
    diameter: float
    tensile_grade: str
    certified: bool

def validate_specs(state: WireRopeState):
    state['certified'] = state['diameter'] > 0 and state['tensile_grade'] != ''
    return state

def safety_check(state: WireRopeState):
    print(f'Performing safety check for rope: {state}')
    return {'certified': state['certified']}

graph = StateGraph(WireRopeState)
graph.add_node('validate', validate_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
