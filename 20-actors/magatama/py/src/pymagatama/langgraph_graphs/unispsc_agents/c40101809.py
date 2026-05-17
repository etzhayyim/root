from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class HeaterProcurementState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: HeaterProcurementState):
    errors = []
    if 'pressure_rating' not in state['specs']: errors.append('Pressure rating missing')
    if 'material' not in state['specs']: errors.append('Material certification required')
    return {'validation_errors': errors, 'approved': len(errors) == 0}

def safety_gate(state: HeaterProcurementState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(HeaterProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()