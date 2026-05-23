from typing import TypedDict
from langgraph.graph import StateGraph, END

class LabKitState(TypedDict):
    product_id: str
    biohazard_level: int
    is_compliant: bool

def validate_biohazard(state: LabKitState):
    state['is_compliant'] = state['biohazard_level'] <= 3
    return state

def check_storage(state: LabKitState):
    print('Verifying cold chain logistics requirements')
    return state

graph = StateGraph(LabKitState)
graph.add_node('validate', validate_biohazard)
graph.add_node('logistics', check_storage)
graph.set_entry_point('validate')
graph.add_edge('validate', 'logistics')
graph.add_edge('logistics', END)
graph = graph.compile()
