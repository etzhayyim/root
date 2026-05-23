from typing import TypedDict
from langgraph.graph import StateGraph, END

class EPROMState(TypedDict):
    part_number: str
    spec_verified: bool
    compliance_check: bool

def validate_spec(state: EPROMState):
    print(f'Checking specs for {state['part_number']}')
    return {'spec_verified': True}

def verify_compliance(state: EPROMState):
    return {'compliance_check': True}

graph = StateGraph(EPROMState)
graph.add_node('validate', validate_spec)
graph.add_node('compliance', verify_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

graph = graph.compile()
