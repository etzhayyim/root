from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    material: str
    inspection_passed: bool
    compliance_docs: list

def validate_material(state: AssemblyState) -> AssemblyState:
    if state['material'] == 'Hastelloy X':
        state['inspection_passed'] = True
    return state

def check_compliance(state: AssemblyState) -> AssemblyState:
    state['compliance_docs'] = ['MTR', 'HeatTreatCert']
    return state

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()