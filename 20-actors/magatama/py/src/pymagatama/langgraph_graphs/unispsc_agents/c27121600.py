from typing import TypedDict
from langgraph.graph import StateGraph, END

class HydraulicProcurementState(TypedDict):
    spec_data: dict
    validation_passed: bool
    export_flag: bool

def validate_specs(state: HydraulicProcurementState):
    pressure = state['spec_data'].get('pressure', 0)
    state['validation_passed'] = pressure > 0 and pressure < 1000
    return state

def export_review(state: HydraulicProcurementState):
    state['export_flag'] = state['spec_data'].get('material') == 'titanium'
    return state

graph = StateGraph(HydraulicProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('export', export_review)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()
