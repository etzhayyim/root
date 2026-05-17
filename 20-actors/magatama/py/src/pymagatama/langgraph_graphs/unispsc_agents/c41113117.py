from typing import TypedDict
from langgraph.graph import StateGraph, END

class GasMonitorState(TypedDict):
    model_id: str
    calibration_status: bool
    is_compliant: bool

def validate_specs(state: GasMonitorState):
    state['is_compliant'] = state['calibration_status'] is True
    return state

def check_compliance(state: GasMonitorState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

workflow = StateGraph(GasMonitorState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', check_compliance, {'compliant': END, 'non_compliant': END})
graph = workflow.compile()