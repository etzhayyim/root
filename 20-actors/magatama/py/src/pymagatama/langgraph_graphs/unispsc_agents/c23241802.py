from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrillingState(TypedDict):
    specs: dict
    validation_passed: bool

def validate_specs(state: DrillingState):
    required = ['spindle_count', 'drilling_capacity']
    passed = all(k in state['specs'] for k in required)
    return {'validation_passed': passed}

def deploy_machine(state: DrillingState):
    print('Proceeding to heavy equipment procurement workflow.')
    return {'validation_passed': True}

graph = StateGraph(DrillingState)
graph.add_node('validator', validate_specs)
graph.add_node('deployer', deploy_machine)
graph.set_entry_point('validator')
graph.add_edge('validator', 'deployer')
graph.add_edge('deployer', END)
graph = graph.compile()