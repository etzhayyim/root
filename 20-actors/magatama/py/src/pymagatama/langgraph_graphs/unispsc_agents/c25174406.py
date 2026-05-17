from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PanelState(TypedDict):
    part_id: str
    specs: dict
    is_validated: bool

def validate_specs(state: PanelState):
    required = ['voltage', 'ip_rating']
    valid = all(k in state['specs'] for k in required)
    return {'is_validated': valid}

def route_by_validation(state: PanelState):
    return 'process' if state['is_validated'] else END

workflow = StateGraph(PanelState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_conditional_edges('validate', route_by_validation, {'process': END, '__end__': END})
graph = workflow.compile()