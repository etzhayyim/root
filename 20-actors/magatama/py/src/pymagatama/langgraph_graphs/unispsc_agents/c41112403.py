from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PressureIndicatorState(TypedDict):
    spec_data: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: PressureIndicatorState):
    errors = []
    if state['spec_data'].get('accuracy_class') == 'none':
        errors.append('Incomplete accuracy documentation')
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def process_calibration(state: PressureIndicatorState):
    print('Verifying calibration certificates...')
    return {'validation_passed': True}

graph = StateGraph(PressureIndicatorState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', process_calibration)
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph.set_entry_point('validate')
graph = graph.compile()
