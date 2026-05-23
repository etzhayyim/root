from typing import TypedDict
from langgraph.graph import StateGraph, END

class TireState(TypedDict):
    tread_spec: str
    compliance_ok: bool
    approved: bool

def validate_tread(state: TireState):
    # Simple logic to validate tread specifications
    if 'depth' in state['tread_spec']:
        return {'compliance_ok': True}
    return {'compliance_ok': False}

def final_approval(state: TireState):
    return {'approved': state['compliance_ok']}

graph = StateGraph(TireState)
graph.add_node('validate', validate_tread)
graph.add_node('approve', final_approval)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
