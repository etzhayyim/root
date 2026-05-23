from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveProcurementState(TypedDict):
    part_type: str
    material_compliance: bool
    pressure_rating: int
    is_compliant: bool

def validate_specs(state: ValveProcurementState):
    state['is_compliant'] = state['pressure_rating'] > 0 and state['material_compliance'] is True
    return state

def approve_workflow(state: ValveProcurementState):
    print(f'Workflow status: Compliant={state['is_compliant']}')
    return state

graph = StateGraph(ValveProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approve_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
