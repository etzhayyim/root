from typing import TypedDict
from langgraph.graph import StateGraph, END

class OpticsState(TypedDict):
    specs: dict
    validated: bool
    compliance_check: bool

def validate_specs(state: OpticsState):
    print('Validating optical specs...')
    state['validated'] = all(k in state['specs'] for k in ['surface_quality', 'coating'])
    return state

def check_export_compliance(state: OpticsState):
    print('Checking dual-use export compliance...')
    state['compliance_check'] = True
    return state

graph = StateGraph(OpticsState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_export_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
