from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BrakeState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: List[str]

def validate_specs(state: BrakeState):
    required = ['material', 'thermal_limit']
    if all(k in state['specs'] for k in required):
        return {'validation_passed': True}
    return {'validation_passed': False, 'error_log': ['Missing required specs']}

def safety_gate(state: BrakeState):
    return 'pass' if state['validation_passed'] else 'fail'

graph = StateGraph(BrakeState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()