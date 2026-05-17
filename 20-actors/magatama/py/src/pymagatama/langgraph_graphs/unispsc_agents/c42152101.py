from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DentalSupplyState(TypedDict):
    material_spec: str
    compliance_docs: List[str]
    validation_passed: bool

def validate_materials(state: DentalSupplyState):
    # Business logic for dental casting ring material conformity
    passed = 'ISO_13485' in state['compliance_docs']
    return {'validation_passed': passed}

def route_by_compliance(state: DentalSupplyState):
    return 'validate' if not state['validation_passed'] else END

graph = StateGraph(DentalSupplyState)
graph.add_node('validate', validate_materials)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()