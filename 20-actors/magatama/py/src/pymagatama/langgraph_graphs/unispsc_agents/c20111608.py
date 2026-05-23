from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class AluminumCastingState(TypedDict):
    part_id: str
    specs: dict
    validation_results: List[str]
    is_approved: bool

def validate_casting_specs(state: AluminumCastingState) -> AluminumCastingState:
    results = []
    if state['specs'].get('tensile_strength_mpa', 0) < 200:
        results.append('Insufficient tensile strength')
    if not state['specs'].get('xray_inspection_standard'):
        results.append('Missing X-ray validation record')
    state['validation_results'] = results
    state['is_approved'] = len(results) == 0
    return state

def route_by_approval(state: AluminumCastingState) -> str:
    return 'approved' if state['is_approved'] else 'rejected'

graph = StateGraph(AluminumCastingState)
graph.add_node('validate', validate_casting_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
