from typing import TypedDict
from langgraph.graph import StateGraph, END

class ImpedanceState(TypedDict):
    device_spec: dict
    is_calibrated: bool
    validation_log: list

def validate_specs(state: ImpedanceState):
    spec = state['device_spec']
    log = []
    if spec.get('frequency_range_hz', 0) > 0:
        log.append('Frequency range valid')
    return {'validation_log': log}

def check_calibration(state: ImpedanceState):
    return {'is_calibrated': state.get('device_spec', {}).get('has_cert', False)}

graph = StateGraph(ImpedanceState)
graph.add_node('validate', validate_specs)
graph.add_node('calibration', check_calibration)
graph.add_edge('validate', 'calibration')
graph.add_edge('calibration', END)
graph.set_entry_point('validate')
graph = graph.compile()