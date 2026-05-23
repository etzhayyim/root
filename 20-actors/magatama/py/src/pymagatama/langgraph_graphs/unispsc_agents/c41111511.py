from typing import TypedDict
from langgraph.graph import StateGraph, END

class ScaleState(TypedDict):
    capacity_tons: float
    iso_compliant: bool
    inspection_result: str

def validate_scale_capacity(state: ScaleState) -> ScaleState:
    if state['capacity_tons'] > 100:
        print('Conducting heavy-load safety review.')
    return state

def check_compliance(state: ScaleState) -> ScaleState:
    state['inspection_result'] = 'PASS' if state['iso_compliant'] else 'FAIL'
    return state

graph = StateGraph(ScaleState)
graph.add_node('validate', validate_scale_capacity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
