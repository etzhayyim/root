from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DuctProcurementState(TypedDict):
    material: str
    diameter: float
    compliance_docs: List[str]
    approved: bool

def validate_specs(state: DuctProcurementState):
    # Business logic for rigid duct validation
    if state['diameter'] > 0 and 'ASTM' in state['compliance_docs']:
        return {'approved': True}
    return {'approved': False}

def perform_inspection(state: DuctProcurementState):
    print('Inspecting rigid duct structural integrity...')
    return state

graph = StateGraph(DuctProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('inspect', perform_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
graph = graph.compile()
