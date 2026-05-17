from typing import TypedDict
from langgraph.graph import StateGraph, END

class SignalConditionerState(TypedDict):
    spec: dict
    validated: bool
    compliance_check: bool

def validate_specs(state: SignalConditionerState):
    state['validated'] = all(k in state['spec'] for k in ['input_range', 'isolation_kv'])
    print('Validating technical specifications...')
    return state

def check_compliance(state: SignalConditionerState):
    state['compliance_check'] = state.get('validated', False)
    print('Checking regulatory compliance for dual-use components...')
    return state

graph = StateGraph(SignalConditionerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()