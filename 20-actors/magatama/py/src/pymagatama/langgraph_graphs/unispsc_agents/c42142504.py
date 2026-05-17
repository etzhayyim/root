from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class BiopsyNeedleState(TypedDict):
    specifications: dict
    validation_passed: bool
    error_logs: List[str]

def validate_specs(state: BiopsyNeedleState):
    required = ['gauge', 'length', 'sterile_cert']
    passed = all(k in state['specifications'] for k in required)
    return {'validation_passed': passed, 'error_logs': [] if passed else ['Missing technical specs']}

def approval_check(state: BiopsyNeedleState):
    return 'approved' if state['validation_passed'] else 'rejected'

graph = StateGraph(BiopsyNeedleState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')