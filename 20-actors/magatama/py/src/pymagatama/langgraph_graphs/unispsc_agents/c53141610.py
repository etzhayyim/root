from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    material: str
    inspection_passed: bool

def validate_holder_material(state: ProcurementState):
    state['inspection_passed'] = state['material'] in ['Plastic', 'Metal', 'Wood']
    return state

def finalize_specification(state: ProcurementState):
    print(f'Finalizing spec for: {state['item_name']}')
    return state

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_holder_material)
graph.add_node('finalize', finalize_specification)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
compile = graph.compile()
