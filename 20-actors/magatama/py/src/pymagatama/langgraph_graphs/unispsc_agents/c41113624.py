from typing import TypedDict, Annotated, List
import operator
from langgraph.graph import StateGraph, END

class TesterState(TypedDict):
    spec_data: dict
    validation_errors: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_specs(state: TesterState):
    errors = []
    if not state['spec_data'].get('Safety Compliance Rating'):
        errors.append('Missing safety compliance rating')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def check_calibration(state: TesterState):
    if not state['spec_data'].get('Calibration Certificate'):
        return {'validation_errors': ['Missing calibration cert']}
    return {}

graph = StateGraph(TesterState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate_check', check_calibration)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate_check')
graph.add_edge('calibrate_check', END)
graph = graph.compile()
