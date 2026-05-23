from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class FastenerState(TypedDict):
    part_number: str
    material_spec: str
    strength_check: bool
    compliance_report: List[str]

def validate_material(state: FastenerState) -> FastenerState:
    # Logic to verify material grade against industry standards
    state['strength_check'] = 'High-Tensile' in state['material_spec']
    state['compliance_report'].append('Material grade validated')
    return state

def generate_cert(state: FastenerState) -> FastenerState:
    if state['strength_check']:
        state['compliance_report'].append('ISO-9001 Certification Generated')
    return state

graph = StateGraph(FastenerState)
graph.add_node('validate', validate_material)
graph.add_node('certify', generate_cert)
graph.set_entry_point('validate')
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph = graph.compile()
