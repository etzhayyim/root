from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class LaminatorProcurementState(TypedDict):
    spec_data: dict
    validation_errors: list
    is_approved: bool

def validate_specs(state: LaminatorProcurementState):
    errors = []
    if state['spec_data'].get('laminating_width_mm', 0) < 200:
        errors.append('Width below industrial standard requirement.')
    return {'validation_errors': errors, 'is_approved': len(errors) == 0}

graph = StateGraph(LaminatorProcurementState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()