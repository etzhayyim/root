from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ThermoformingState(TypedDict):
    material_type: str
    thickness_mm: float
    compliance_certs: List[str]
    validated: bool

def validate_materials(state: ThermoformingState):
    required = ['RoHS', 'ISO-9001']
    all_present = all(cert in state['compliance_certs'] for cert in required)
    return { 'validated': all_present and state['thickness_mm'] > 0 }

graph = StateGraph(ThermoformingState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
app = graph.compile()
