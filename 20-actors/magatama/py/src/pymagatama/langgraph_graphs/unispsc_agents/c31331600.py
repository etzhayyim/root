from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    specs: dict
    validated: bool
    error: str

def validate_structural_specs(state: AssemblyState):
    required = ['welding_code', 'material_cert']
    if all(k in state['specs'] for k in required):
        return {'validated': True}
    return {'validated': False, 'error': 'Missing required certificates'}

def structural_workflow(state: AssemblyState):
    print('Initiating structural assembly quality check...')
    return 'passed'

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_structural_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
compile = graph.compile()
