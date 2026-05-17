from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    api_name: str
    purity_level: float
    gmp_valid: bool
    status: str

def validate_api_specs(state: ProcurementState):
    if state['purity_level'] >= 99.9 and state['gmp_valid']:
        return {'status': 'APPROVED'}
    return {'status': 'REJECTED'}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_api_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()