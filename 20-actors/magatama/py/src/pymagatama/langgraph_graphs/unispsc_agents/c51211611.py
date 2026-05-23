from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrientineState(TypedDict):
    batch_number: str
    purity_level: float
    storage_temp: float
    is_compliant: bool

def validate_quality(state: TrientineState):
    state['is_compliant'] = state['purity_level'] >= 99.5 and state['storage_temp'] <= 25.0
    return state

def shipment_approval(state: TrientineState):
    print(f"Processing batch {state['batch_number']} status: {state['is_compliant']}")
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(TrientineState)
graph.add_node("validate", validate_quality)
graph.add_node("ship", shipment_approval)
graph.set_entry_point("validate")
graph.add_edge("validate", "ship")
graph.add_edge("ship", END)
graph = graph.compile()
