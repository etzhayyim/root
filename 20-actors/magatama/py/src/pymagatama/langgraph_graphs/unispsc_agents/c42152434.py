from typing import TypedDict
from langgraph.graph import StateGraph, END

class AmalgamatorState(TypedDict):
    device_specs: dict
    compliance_check: bool
    approved: bool

def validate_specs(state: AmalgamatorState):
    freq = state['device_specs'].get('frequency', 0)
    state['compliance_check'] = 3000 <= freq <= 5000
    return {'compliance_check': state['compliance_check']}

def approval_logic(state: AmalgamatorState):
    state['approved'] = state['compliance_check']
    return {'approved': state['approved']}

graph = StateGraph(AmalgamatorState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_logic)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()