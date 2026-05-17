from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TerminalState(TypedDict):
    device_id: str
    specs: dict
    validation_passed: bool
    error_log: List[str]

def validate_specs(state: TerminalState):
    required = ['IP_Rating', 'Operating_System_Version']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def route_by_validation(state: TerminalState):
    return 'validate' if not state.get('validation_passed') else END

graph = StateGraph(TerminalState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()