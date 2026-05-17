from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MicrofilmGraphState(TypedDict):
    equipment_id: str
    specs: dict
    validation_results: List[str]

def validate_optical_resolution(state: MicrofilmGraphState) -> MicrofilmGraphState:
    dpi = state['specs'].get('dpi', 0)
    if dpi >= 600:
        state['validation_results'].append('Resolution compliant')
    return state

def check_maintenance(state: MicrofilmGraphState) -> MicrofilmGraphState:
    if 'contract' in state['specs']:
        state['validation_results'].append('Service contract active')
    return state

graph = StateGraph(MicrofilmGraphState)
graph.add_node('validate_optics', validate_optical_resolution)
graph.add_node('check_service', check_maintenance)
graph.set_entry_point('validate_optics')
graph.add_edge('validate_optics', 'check_service')
graph.add_edge('check_service', END)
graph = graph.compile()