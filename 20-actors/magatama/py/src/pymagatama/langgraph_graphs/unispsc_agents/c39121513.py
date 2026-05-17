from typing import TypedDict
from langgraph.graph import StateGraph, END

class SwitchState(TypedDict):
    spec_sheet: dict
    validation_passed: bool

def validate_specs(state: SwitchState):
    required = ['voltage', 'current', 'poles']
    state['validation_passed'] = all(k in state['spec_sheet'] for k in required)
    return state

def check_compliance(state: SwitchState):
    if state.get('validation_passed'):
        print('Compliance check: Checking RoHS and UL status.')
    return 'end'

graph = StateGraph(SwitchState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()