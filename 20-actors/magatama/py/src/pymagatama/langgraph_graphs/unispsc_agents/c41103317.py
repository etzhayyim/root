from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcessingState(TypedDict):
    instrument_spec: dict
    calibrated: bool
    validation_errors: List[str]

def validate_specs(state: ProcessingState):
    errors = []
    if 'measurement_range' not in state['instrument_spec']: errors.append('Range missing')
    return {'validation_errors': errors}

def check_calibration(state: ProcessingState):
    return {'calibrated': state['instrument_spec'].get('needs_cal', False)}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_specs)
graph.add_node('calibration', check_calibration)
graph.add_edge('validate', 'calibration')
graph.add_edge('calibration', END)
graph.set_entry_point('validate')
graph = graph.compile()
