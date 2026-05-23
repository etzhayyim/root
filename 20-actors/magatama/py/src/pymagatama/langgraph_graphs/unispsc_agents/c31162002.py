from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: ProcurementState):
    errors = []
    if not state['spec_data'].get('cap_diameter'): errors.append('Missing cap diameter')
    if not state['spec_data'].get('shank_length'): errors.append('Missing shank length')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

workflow = StateGraph(ProcurementState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
