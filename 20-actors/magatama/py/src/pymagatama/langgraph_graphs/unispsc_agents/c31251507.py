from typing import TypedDict
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_data: dict
    validated: bool
    export_flag: bool

def validate_specs(state: ActuatorState):
    torque = state['spec_data'].get('torque', 0)
    state['validated'] = torque > 0
    return state

def check_export_controls(state: ActuatorState):
    state['export_flag'] = state['spec_data'].get('high_precision', False)
    return state

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('export_check', check_export_controls)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_check')
graph.add_edge('export_check', END)
graph = graph.compile()