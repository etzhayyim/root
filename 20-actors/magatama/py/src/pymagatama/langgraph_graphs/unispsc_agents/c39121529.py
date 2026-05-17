from typing import TypedDict
from langgraph.graph import StateGraph, END

class ContactorState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_electrical_specs(state: ContactorState):
    voltage = state['spec_data'].get('voltage', 0)
    state['validation_passed'] = voltage > 0
    return state

def run_compliance_check(state: ContactorState):
    print('Checking regulatory compliance for contactor...')
    return state

graph = StateGraph(ContactorState)
graph.add_node('validate', validate_electrical_specs)
graph.add_node('compliance', run_compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()