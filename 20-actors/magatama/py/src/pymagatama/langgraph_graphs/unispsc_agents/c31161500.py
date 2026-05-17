from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ScrewState(TypedDict):
    spec: dict
    validated: bool
    error: str

def validate_screw_specs(state: ScrewState):
    required = ['material_grade', 'thread_standard', 'diameter']
    valid = all(key in state['spec'] for key in required)
    return {'validated': valid, 'error': None if valid else 'Missing mandatory specifications'}

def check_compliance(state: ScrewState):
    if not state.get('validated'):
        return 'error_node'
    return 'success_node'

graph = StateGraph(ScrewState)
graph.add_node('validate', validate_screw_specs)
graph.add_node('success_node', lambda x: x)
graph.add_node('error_node', lambda x: x)
graph.set_entry_point('validate')
graph.add_edge('validate', 'success_node')
graph.add_edge('validate', 'error_node')
app = graph.compile()