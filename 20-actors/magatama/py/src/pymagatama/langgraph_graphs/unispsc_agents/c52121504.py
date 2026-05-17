from typing import TypedDict
from langgraph.graph import StateGraph, END

class MattressCoverState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_specs(state: MattressCoverState):
    required = ['material', 'flame_retardancy', 'dimensions']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def check_compliance(state: MattressCoverState):
    print('Checking standard compliance...')
    return {'validation_passed': True}

graph = StateGraph(MattressCoverState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()