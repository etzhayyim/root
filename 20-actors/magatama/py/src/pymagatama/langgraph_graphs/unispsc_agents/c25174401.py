from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BezelState(TypedDict):
    part_specs: dict
    validation_passed: bool
    compliance_report: str

def validate_specs(state: BezelState):
    # Perform dimensional validation logic here
    state['validation_passed'] = 'dimension' in state['part_specs']
    return state

def check_compliance(state: BezelState):
    state['compliance_report'] = 'ISO-9001:2015 compliant' if state['validation_passed'] else 'Failed'
    return state

graph = StateGraph(BezelState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
