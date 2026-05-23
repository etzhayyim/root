from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DetectorState(TypedDict):
    model_id: str
    currency_supported: List[str]
    needs_calibration: bool
    validation_passed: bool

def validate_specs(state: DetectorState):
    state['validation_passed'] = bool(state['model_id'] and state['currency_supported'])
    print(f'Validating specs for {state['model_id']}')
    return 'process_calibration' if state['needs_calibration'] else END

def calibrate_device(state: DetectorState):
    print('Performing sensor calibration protocol...')
    state['needs_calibration'] = False
    return END

graph = StateGraph(DetectorState)
graph.add_node('validate', validate_specs)
graph.add_node('process_calibration', calibrate_device)
graph.set_entry_point('validate')
graph.add_edge('process_calibration', END)
