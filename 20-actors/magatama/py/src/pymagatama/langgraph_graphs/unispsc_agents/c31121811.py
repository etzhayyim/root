from langgraph.graph import StateGraph, END
from typing import TypedDict

class ProcurementState(TypedDict):
    material: str
    tolerance: float
    inspection_passed: bool

def validate_specs(state: ProcurementState):
    state['inspection_passed'] = state['tolerance'] < 0.05
    return 'processed'

def process_casting(state: ProcurementState):
    return f'Casting {state['material']} processed.'

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('cast', process_casting)
graph.add_edge('validate', 'cast')
graph.add_edge('cast', END)
graph.set_entry_point('validate')
graph = graph.compile()
