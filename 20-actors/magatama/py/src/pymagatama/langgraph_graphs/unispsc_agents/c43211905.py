from typing import TypedDict
from langgraph.graph import StateGraph, END

class OLEDProcurementState(TypedDict):
    panel_specs: dict
    validation_passed: bool
    export_control_check: bool

def validate_specs(state: OLEDProcurementState):
    specs = state['panel_specs']
    passed = 'Resolution' in specs and 'Brightness_nits' in specs
    return {'validation_passed': passed}

def check_compliance(state: OLEDProcurementState):
    # Simulate dual-use export control check
    return {'export_control_check': True}

graph = StateGraph(OLEDProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
