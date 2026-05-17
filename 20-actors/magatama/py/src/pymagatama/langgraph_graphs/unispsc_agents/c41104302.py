from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CultureProcessState(TypedDict):
    device_id: str
    process_params: dict
    validation_checks: List[str]
    is_compliant: bool

def validate_specs(state: CultureProcessState):
    required = ['sterilization_method', 'capacity']
    state['is_compliant'] = all(k in state['process_params'] for k in required)
    return state

def perform_safety_check(state: CultureProcessState):
    state['validation_checks'].append('bio-safety-level-verification')
    return state

workflow = StateGraph(CultureProcessState)
workflow.add_node('specs', validate_specs)
workflow.add_node('safety', perform_safety_check)
workflow.add_edge('specs', 'safety')
workflow.add_edge('safety', END)
workflow.set_entry_point('specs')
graph = workflow.compile()