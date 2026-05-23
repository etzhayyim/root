from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BioMaterialState(TypedDict):
    material_name: str
    purity_level: float
    gmp_compliant: bool
    validation_passed: bool

def check_gmp_status(state: BioMaterialState) -> BioMaterialState:
    state['validation_passed'] = state['gmp_compliant'] and state['purity_level'] >= 0.98
    return state

graph = StateGraph(BioMaterialState)
graph.add_node('verify_compliance', check_gmp_status)
graph.set_entry_point('verify_compliance')
graph.add_edge('verify_compliance', END)

app = graph.compile()
