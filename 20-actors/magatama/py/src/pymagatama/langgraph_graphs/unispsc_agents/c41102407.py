from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WarmingCabinetState(TypedDict):
    specs: dict
    validation_errors: List[str]
    approved: bool

def validate_specs(state: WarmingCabinetState):
    errors = []
    if 'temp_range' not in state['specs']: errors.append('Missing temp_range')
    if 'certification' not in state['specs']: errors.append('Missing medical certification')
    return {'validation_errors': errors}

def approval_node(state: WarmingCabinetState):
    return {'approved': len(state['validation_errors']) == 0}

graph = StateGraph(WarmingCabinetState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
app = graph.compile()
