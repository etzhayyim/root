from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CableProcurementState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    approved: bool

def validate_tensile_strength(state: CableProcurementState):
    errors = []
    if state['spec_data'].get('tensile_strength', 0) < 1770:
        errors.append('Tensile strength below minimum safety threshold.')
    return {'validation_errors': errors}

workflow = StateGraph(CableProcurementState)
workflow.add_node('validate', validate_tensile_strength)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
