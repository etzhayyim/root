from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class IVKitState(TypedDict):
    kit_id: str
    is_sterile: bool
    is_expired: bool
    validation_logs: List[str]

def validate_sterility(state: IVKitState):
    log = 'Sterility check passed' if state['is_sterile'] else 'Sterility check failed'
    return {'validation_logs': [log]}

def validate_expiry(state: IVKitState):
    log = 'Expiry validation: OK' if not state['is_expired'] else 'Expiry validation: EXPIRED'
    return {'validation_logs': [log]}

graph = StateGraph(IVKitState)
graph.add_node('check_sterility', validate_sterility)
graph.add_node('check_expiry', validate_expiry)
graph.set_entry_point('check_sterility')
graph.add_edge('check_sterility', 'check_expiry')
graph.add_edge('check_expiry', END)

app = graph.compile()