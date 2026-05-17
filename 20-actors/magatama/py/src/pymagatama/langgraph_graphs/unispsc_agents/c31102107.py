from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CastingState(TypedDict):
    part_id: str
    specs: dict
    validated: bool
    error_logs: List[str]

def validate_materials(state: CastingState):
    # Simulate material compliance check against aerospace standards
    state['validated'] = True if 'grade' in state['specs'] else False
    return state

def check_dimensions(state: CastingState):
    # Simulate geometric dimensioning GD&T validation
    state['validated'] = state['validated'] and (state['specs'].get('tolerance') == 'tight')
    return state

graph = StateGraph(CastingState)
graph.add_node('material_check', validate_materials)
graph.add_node('dimension_check', check_dimensions)
graph.set_entry_point('material_check')
graph.add_edge('material_check', 'dimension_check')
graph.add_edge('dimension_check', END)
graph = graph.compile()