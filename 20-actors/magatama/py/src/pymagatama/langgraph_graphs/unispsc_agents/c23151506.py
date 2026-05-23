from typing import TypedDict
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    specs: dict
    validated: bool
    compliance_check: bool

def validate_specs(state: ActuatorState):
    required = ['torque', 'accuracy']
    state['validated'] = all(k in state['specs'] for k in required)
    return state

def compliance_check(state: ActuatorState):
    state['compliance_check'] = state.get('validated', False)
    return state

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
