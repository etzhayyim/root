from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitState(TypedDict):
    kit_id: str
    contents: List[str]
    sterility_verified: bool
    compliance_check: bool

def validate_contents(state: KitState):
    required = ['catheter', 'syringe', 'needle', 'drape']
    return {'compliance_check': all(item in state['contents'] for item in required)}

def verify_sterility(state: KitState):
    return {'sterility_verified': True}

graph = StateGraph(KitState)
graph.add_node('validate', validate_contents)
graph.add_node('sterility', verify_sterility)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sterility')
graph.add_edge('sterility', END)
graph = graph.compile()