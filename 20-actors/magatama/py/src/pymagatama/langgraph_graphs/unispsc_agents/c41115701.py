from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DetectorState(TypedDict):
    model_id: str
    specs: dict
    validation_status: bool
    export_control_check: bool

def validate_specs(state: DetectorState):
    state['validation_status'] = 'detection_limit' in state['specs'] and 'calibration' in state['specs']
    return state

def check_export_controls(state: DetectorState):
    state['export_control_check'] = True
    return state

graph = StateGraph(DetectorState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_controls)
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph.set_entry_point('validate')
graph = graph.compile()