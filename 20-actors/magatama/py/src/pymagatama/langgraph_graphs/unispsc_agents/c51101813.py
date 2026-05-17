from typing import TypedDict
from langgraph.graph import StateGraph, END

class ChemicalState(TypedDict):
    purity: float
    cas_verified: bool
    gmp_compliant: bool
    status: str

def validate_compliance(state: ChemicalState):
    if state['purity'] >= 99.0 and state['gmp_compliant']:
        return {'status': 'APPROVED'}
    return {'status': 'REJECTED'}

def route_by_status(state: ChemicalState):
    return state['status']

graph = StateGraph(ChemicalState)
graph.add_node('validate', validate_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile_graph = graph.compile()