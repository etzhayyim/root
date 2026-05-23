from typing import TypedDict
from langgraph.graph import StateGraph, END

class VarnishState(TypedDict):
    viscosity: float
    voc_level: float
    compliance_check: bool
    approved: bool

def validate_specs(state: VarnishState):
    state['compliance_check'] = state['voc_level'] < 5.0
    return {'compliance_check': state['compliance_check']}

def approval_step(state: VarnishState):
    state['approved'] = state['compliance_check'] and state['viscosity'] > 100
    return {'approved': state['approved']}

graph = StateGraph(VarnishState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_step)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
