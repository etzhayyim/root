from typing import TypedDict
from langgraph.graph import StateGraph, END

class NeedleState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_needle_specs(state: NeedleState):
    required = ['gauge', 'material', 'sterilization']
    valid = all(k in state['specs'] for k in required)
    return {'is_compliant': valid}

def update_status(state: NeedleState):
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(NeedleState)
graph.add_node('validate', validate_needle_specs)
graph.add_node('status', update_status)
graph.set_entry_point('validate')
graph.add_edge('validate', 'status')
graph.add_edge('status', END)
graph = graph.compile()