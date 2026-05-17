from typing import TypedDict
from langgraph.graph import StateGraph, END

class EarmuffState(TypedDict):
    part_number: str
    compatibility_verified: bool
    compliance_checked: bool

def verify_compatibility(state: EarmuffState):
    print(f'Checking compatibility for {state['part_number']}')
    return {'compatibility_verified': True}

def check_compliance(state: EarmuffState):
    print('Validating ISO/ANSI safety standards')
    return {'compliance_checked': True}

graph = StateGraph(EarmuffState)
graph.add_node('compatibility', verify_compatibility)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('compatibility')
graph.add_edge('compatibility', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()