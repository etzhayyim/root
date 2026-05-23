from typing import TypedDict
from langgraph.graph import StateGraph, END

class ThermalState(TypedDict):
    spec_compliance: bool
    thermal_rating: float
    has_msds: bool

def validate_density(state: ThermalState) -> ThermalState:
    state['spec_compliance'] = state['thermal_rating'] >= 1000.0
    return state

def check_compliance(state: ThermalState) -> str:
    return 'process' if state['has_msds'] and state['spec_compliance'] else 'reject'

graph = StateGraph(ThermalState)
graph.add_node('validate', validate_density)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'process': END, 'reject': END})
graph.compile()
