from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ElectronicLoadState(TypedDict):
    specs: dict
    validation_passed: bool
    errors: List[str]

def validate_specs(state: ElectronicLoadState):
    required_keys = ['Voltage Range', 'Power Rating', 'Operating Modes']
    errors = [key for key in required_keys if key not in state['specs']]
    return {'validation_passed': len(errors) == 0, 'errors': errors}

def route_by_validation(state: ElectronicLoadState):
    if state['validation_passed']:
        return 'final'
    return 'error_handling'

graph = StateGraph(ElectronicLoadState)
graph.add_node('validate', validate_specs)
graph.add_node('final', lambda state: state)
graph.add_node('error_handling', lambda state: state)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation)
graph.add_edge('final', END)
graph.add_edge('error_handling', END)
graph = graph.compile()