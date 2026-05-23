from typing import TypedDict
from langgraph.graph import StateGraph, END

class DistributionState(TypedDict):
    spec_data: dict
    validation_status: bool
    error_log: list

def validate_specs(state: DistributionState):
    required = ['Pressure Rating', 'Material Composition']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validation_status': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: DistributionState):
    return 'valid' if state['validation_status'] else 'invalid'

workflow = StateGraph(DistributionState)
workflow.add_node('validator', validate_specs)
workflow.add_edge('validator', END)
workflow.set_entry_point('validator')
graph = workflow.compile()
