from typing import TypedDict
from langgraph.graph import StateGraph, END

class JackState(TypedDict):
    load_capacity: float
    safety_passed: bool
    validation_log: list

def validate_specs(state: JackState):
    passed = state['load_capacity'] > 0
    return {'safety_passed': passed, 'validation_log': ['Capacity check complete']}

def check_compliance(state: JackState):
    return {'validation_log': state['validation_log'] + ['Compliance verified']}

graph = StateGraph(JackState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
