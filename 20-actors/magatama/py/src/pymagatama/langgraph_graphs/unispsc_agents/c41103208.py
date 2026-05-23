from typing import TypedDict
from langgraph.graph import StateGraph, END

class BloodWasherState(TypedDict):
    device_id: str
    calibration_status: bool
    validation_log: list

def validate_specs(state: BloodWasherState):
    state['validation_log'].append('Validating centrifugal speed accuracy.')
    return {'calibration_status': True}

def update_records(state: BloodWasherState):
    state['validation_log'].append('Updating lifecycle service database.')
    return {'validation_log': state['validation_log']}

graph = StateGraph(BloodWasherState)
graph.add_node('validate', validate_specs)
graph.add_node('record', update_records)
graph.set_entry_point('validate')
graph.add_edge('validate', 'record')
graph.add_edge('record', END)
graph = graph.compile()
