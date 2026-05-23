from typing import TypedDict
from langgraph.graph import StateGraph, END

class MousePadState(TypedDict):
    spec_data: dict
    validation_result: bool
    error_log: list

def validate_dimensions(state: MousePadState):
    dims = state['spec_data'].get('dimensions', {})
    valid = dims.get('width', 0) > 0 and dims.get('height', 0) > 0
    return {'validation_result': valid, 'error_log': [] if valid else ['Invalid dimensions']}

def check_compliance(state: MousePadState):
    compliant = state['spec_data'].get('rohs_compliant', False)
    return {'validation_result': state['validation_result'] and compliant}

workflow = StateGraph(MousePadState)
workflow.add_node('validate_dim', validate_dimensions)
workflow.add_node('check_comp', check_compliance)
workflow.add_edge('validate_dim', 'check_comp')
workflow.add_edge('check_comp', END)
workflow.set_entry_point('validate_dim')
graph = workflow.compile()
