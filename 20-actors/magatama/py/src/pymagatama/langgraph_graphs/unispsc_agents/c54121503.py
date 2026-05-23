from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GemState(TypedDict):
    gem_type: str
    certificate_id: str
    is_verified: bool
    value: float

def validate_gemstone(state: GemState):
    print(f'Validating gemstone certification: {state['certificate_id']}')
    return {'is_verified': True}

def audit_value(state: GemState):
    print(f'Auditing high-value asset: {state['value']}')
    return {'is_verified': True}

graph = StateGraph(GemState)
graph.add_node('verify', validate_gemstone)
graph.add_node('audit', audit_value)
graph.add_edge('verify', 'audit')
graph.add_edge('audit', END)
graph.set_entry_point('verify')
compiled_graph = graph.compile()
