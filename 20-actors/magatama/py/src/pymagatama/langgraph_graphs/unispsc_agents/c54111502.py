from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WatchProcurementState(TypedDict):
    model_id: str
    quality_cert: bool
    is_authentic: bool
    inspection_passed: bool

def validate_authenticity(state: WatchProcurementState):
    state['is_authentic'] = True if state['model_id'] else False
    return {'is_authentic': state['is_authentic']}

def conduct_quality_inspection(state: WatchProcurementState):
    state['inspection_passed'] = state['quality_cert'] and state['is_authentic']
    return {'inspection_passed': state['inspection_passed']}

graph = StateGraph(WatchProcurementState)
graph.add_node('validate', validate_authenticity)
graph.add_node('inspect', conduct_quality_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'inspect')
graph.add_edge('inspect', END)
app = graph.compile()