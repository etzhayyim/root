from typing import TypedDict
from langgraph.graph import StateGraph, END

class RadiationShieldingState(TypedDict):
    purity: float
    thickness: float
    compliance_checked: bool
    approved: bool

def validate_purity(state: RadiationShieldingState):
    state['compliance_checked'] = state['purity'] >= 99.9
    return state

def safety_gate(state: RadiationShieldingState):
    state['approved'] = state['compliance_checked'] and state['thickness'] > 0
    return {'approved': state['approved']}

graph = StateGraph(RadiationShieldingState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', safety_gate)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
app = graph.compile()