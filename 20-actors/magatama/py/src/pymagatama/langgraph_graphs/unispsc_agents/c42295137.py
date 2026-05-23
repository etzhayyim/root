from typing import TypedDict
from langgraph.graph import StateGraph, END

class GastroState(TypedDict):
    device_id: str
    compliance_validated: bool
    sterility_check: bool

def validate_compliance(state: GastroState):
    print(f'Checking compliance for {state['device_id']}')
    return {'compliance_validated': True}

def verify_sterility(state: GastroState):
    print('Verifying sterile packaging integrity')
    return {'sterility_check': True}

graph = StateGraph(GastroState)
graph.add_node('compliance', validate_compliance)
graph.add_node('sterility', verify_sterility)
graph.add_edge('compliance', 'sterility')
graph.add_edge('sterility', END)
graph.set_entry_point('compliance')
graph = graph.compile()
