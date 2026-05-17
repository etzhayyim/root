from typing import TypedDict
from langgraph.graph import StateGraph, END

class IronBarState(TypedDict):
    spec_data: dict
    validated: bool
    error: str

def validate_specs(state: IronBarState):
    specs = state['spec_data']
    required_keys = ['material_grade', 'diameter', 'tensile_strength']
    all_present = all(k in specs for k in required_keys)
    return {'validated': all_present, 'error': '' if all_present else 'Missing requirements'}

def structural_integrity_check(state: IronBarState):
    if state.get('validated'):
        print('Performing integrity validation...')
    return state

graph = StateGraph(IronBarState)
graph.add_node('validate', validate_specs)
graph.add_node('integrity', structural_integrity_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'integrity')
graph.add_edge('integrity', END)
compile = graph.compile()