from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcurementState(TypedDict):
    item_name: str
    spec_requirements: dict
    validation_passed: bool
    error_logs: List[str]

def validate_pen_specs(state: ProcurementState):
    errors = []
    if not state['spec_requirements'].get('cable_length_mm'):
        errors.append('Missing cable length requirement')
    return {'validation_passed': len(errors) == 0, 'error_logs': errors}

def finalize_procurement(state: ProcurementState):
    print('Finalizing secured pen procurement workflow...')
    return {'validation_passed': True}

graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_pen_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()