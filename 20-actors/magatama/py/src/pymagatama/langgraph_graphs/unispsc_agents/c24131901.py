from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class IceMakerState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_capacity(state: IceMakerState):
    capacity = state['specs'].get('capacity', 0)
    if capacity < 20:
        state['validation_errors'].append('Insufficient capacity for commercial use')
    return state

def check_compliance(state: IceMakerState):
    if 'cert' not in state['specs']:
        state['validation_errors'].append('Missing safety certification')
    else:
        state['approved'] = True
    return state

graph = StateGraph(IceMakerState)
graph.add_node('capacity_check', validate_capacity)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('capacity_check')
graph.add_edge('capacity_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()