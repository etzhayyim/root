from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    specs: dict
    is_validated: bool
    error_log: list

def validate_specs(state: AssemblyState):
    required = ['material_grade', 'rivet_type']
    valid = all(k in state['specs'] for k in required)
    return {'is_validated': valid}

def process_assembly(state: AssemblyState):
    if state['is_validated']:
        return {'error_log': [], 'is_validated': True}
    return {'error_log': ['Missing critical structural specs'], 'is_validated': False}

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_assembly)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()