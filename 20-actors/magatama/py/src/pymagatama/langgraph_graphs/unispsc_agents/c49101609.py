from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class OrnamentState(TypedDict):
    item_name: str
    material_safety_verified: bool
    compliance_passed: bool

def validate_safety(state: OrnamentState):
    print(f'Checking safety for {state["item_name"]}')
    return {'material_safety_verified': True}

def check_compliance(state: OrnamentState):
    print('Performing regulatory compliance audit')
    return {'compliance_passed': True}

graph = StateGraph(OrnamentState)
graph.add_node('safety_check', validate_safety)
graph.add_node('compliance_check', check_compliance)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'compliance_check')
graph.add_edge('compliance_check', END)
graph = graph.compile()
