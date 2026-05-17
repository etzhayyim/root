from typing import TypedDict
from langgraph.graph import StateGraph, END

class ThyratronState(TypedDict):
    spec_data: dict
    validation_passed: bool
    export_control_check: bool

def validate_specs(state: ThyratronState):
    # Core logic for voltage rating compliance
    voltage = state['spec_data'].get('peak_anode_voltage_kv', 0)
    valid = voltage > 0
    return {'validation_passed': valid}

def check_export_compliance(state: ThyratronState):
    # Dual-use classification logic
    state['export_control_check'] = True
    return state

graph = StateGraph(ThyratronState)
graph.add_node('validate', validate_specs)
graph.add_node('export_review', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()