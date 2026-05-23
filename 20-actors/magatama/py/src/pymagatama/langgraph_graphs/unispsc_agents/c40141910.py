from typing import TypedDict
from langgraph.graph import StateGraph, END

class DuctState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_specs(state: DuctState):
    required = ['Material Grade', 'Duct Thickness']
    missing = [f for f in required if f not in state['spec_data']]
    return {'validation_passed': len(missing) == 0, 'error_log': missing}

def route_by_validation(state: DuctState):
    return 'process' if state['validation_passed'] else END

graph = StateGraph(DuctState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: {'error_log': ['Proceeding with procurement']})
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('process', END)
graph = graph.compile()
