from typing import TypedDict
from langgraph.graph import StateGraph, END

class IrrigationState(TypedDict):
    batch_id: str
    is_sterile: bool
    is_expired: bool

def validate_sterile(state: IrrigationState):
    state['is_sterile'] = True
    return 'valid' if state['is_sterile'] else 'invalid'

def check_expiry(state: IrrigationState):
    state['is_expired'] = False
    return 'ok' if not state['is_expired'] else 'reject'

graph = StateGraph(IrrigationState)
graph.add_node('certify', validate_sterile)
graph.add_node('expiry', check_expiry)
graph.set_entry_point('certify')
graph.add_edge('certify', 'expiry')
graph.add_edge('expiry', END)
graph = graph.compile()
