from typing import TypedDict
from langgraph.graph import StateGraph, END

class SolventState(TypedDict):
    product_id: str
    flash_point: float
    voc_compliant: bool
    approved: bool

def validate_safety(state: SolventState):
    state['approved'] = state['flash_point'] > 20.0 and state['voc_compliant']
    return {'approved': state['approved']}

graph = StateGraph(SolventState)
graph.add_node('safety_check', validate_safety)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', END)
graph = graph.compile()
