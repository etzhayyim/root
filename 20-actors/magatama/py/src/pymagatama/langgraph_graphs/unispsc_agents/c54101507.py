from typing import TypedDict
from langgraph.graph import StateGraph, END

class TiaraState(TypedDict):
    material_certified: bool
    inspection_passed: bool
    qc_score: float

def validate_materials(state: TiaraState):
    state['material_certified'] = True
    return state

def run_qc(state: TiaraState):
    state['inspection_passed'] = state['qc_score'] > 0.8
    return state

graph = StateGraph(TiaraState)
graph.add_node('validate', validate_materials)
graph.add_node('qc', run_qc)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()