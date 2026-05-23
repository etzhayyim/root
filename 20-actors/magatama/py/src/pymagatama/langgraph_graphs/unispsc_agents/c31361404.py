from typing import TypedDict
from langgraph.graph import StateGraph, END

class AssemblyState(TypedDict):
    spec_data: dict
    certified: bool
    approved: bool

def validate_specs(state: AssemblyState):
    required = ['WPS', 'NDT', 'Material_Spec']
    state['certified'] = all(k in state['spec_data'] for k in required)
    return state

def check_compliance(state: AssemblyState):
    state['approved'] = state['certified'] and state['spec_data'].get('pressure_tested', False)
    return state

graph = StateGraph(AssemblyState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
