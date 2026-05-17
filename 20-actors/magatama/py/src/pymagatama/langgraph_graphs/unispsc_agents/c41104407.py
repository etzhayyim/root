from typing import TypedDict
from langgraph.graph import StateGraph, END

class IncubatorState(TypedDict):
    specs: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: IncubatorState):
    required = ['temp_accuracy', 'co2_level']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed, 'error_log': [] if passed else ['Missing specs']}

def approval_workflow(state: IncubatorState):
    return {'validation_passed': True}

graph = StateGraph(IncubatorState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_workflow)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
app = graph.compile()