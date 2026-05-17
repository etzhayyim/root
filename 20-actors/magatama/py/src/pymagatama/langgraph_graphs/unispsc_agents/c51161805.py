from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    material_name: str
    purity_level: float
    gmp_certified: bool
    validation_status: str

def validate_carbocisteine(state: PharmState):
    if state['purity_level'] < 98.0:
        return {'validation_status': 'REJECTED'}
    if not state.get('gmp_certified', False):
        return {'validation_status': 'PENDING_GMP_REVIEW'}
    return {'validation_status': 'APPROVED'}

graph = StateGraph(PharmState)
graph.add_node('validate', validate_carbocisteine)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()