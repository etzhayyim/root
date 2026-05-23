from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PipeState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_material(state: PipeState):
    # Business logic for non-metallic rivet validation
    state['is_compliant'] = 'material' in state['specs']
    return state

def check_integrity(state: PipeState):
    # Business logic for riveting process check
    state['is_compliant'] = state.get('is_compliant', False) and 'rivet_strength' in state['specs']
    return state

graph = StateGraph(PipeState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_integrity', check_integrity)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_integrity')
graph.add_edge('check_integrity', END)
graph = graph.compile()
