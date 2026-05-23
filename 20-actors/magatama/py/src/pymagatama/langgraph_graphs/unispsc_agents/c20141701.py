from typing import TypedDict
from langgraph.graph import StateGraph, END

class ServoProcurementState(TypedDict):
    spec_sheet: dict
    validation_results: dict

def validate_specs(state: ServoProcurementState):
    # Business logic for technical validation
    return {'validation_results': {'passed': True if state['spec_sheet'].get('IP') == 'IP67' else False}}

def check_export_compliance(state: ServoProcurementState):
    # Dual-use logic
    return {'validation_results': {'export_ok': True}}

graph = StateGraph(ServoProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
