from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AnalysisState(TypedDict):
    device_specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: AnalysisState):
    errors = []
    if 'calibration_date' not in state['device_specs']:
        errors.append('Missing calibration certification')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

graph = StateGraph(AnalysisState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()