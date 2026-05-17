from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class StrobeState(TypedDict):
    model_number: str
    fpm_range: List[float]
    calibration_status: bool
    is_compliant: bool

def validate_specs(state: StrobeState):
    state['is_compliant'] = state['fpm_range'][1] > 1000 and state['calibration_status']
    return state

def check_compliance(state: StrobeState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(StrobeState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'compliant': END, 'non_compliant': END})
graph = graph.compile()