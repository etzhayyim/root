from typing import TypedDict
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    material_spec: str
    inspection_report: dict
    approved: bool

def validate_material(state: CastingState):
    state['approved'] = 'ASTM' in state['material_spec']
    return state

def check_quality(state: CastingState):
    if state.get('inspection_report', {}).get('passed', False):
        state['approved'] = True
    return state

graph = StateGraph(CastingState)
graph.add_node('validate', validate_material)
graph.add_node('inspect', check_quality)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
