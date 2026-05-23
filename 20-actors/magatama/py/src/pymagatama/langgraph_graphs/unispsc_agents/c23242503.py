from typing import TypedDict
from langgraph.graph import StateGraph, END

class MillingMachineState(TypedDict):
    specs: dict
    validation_passed: bool
    export_license_required: bool

def validate_specs(state: MillingMachineState):
    state['validation_passed'] = all(k in state['specs'] for k in ['rpm', 'accuracy'])
    return state

def check_export_compliance(state: MillingMachineState):
    state['export_license_required'] = state['specs'].get('precision', 0) < 0.005
    return state

graph = StateGraph(MillingMachineState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
