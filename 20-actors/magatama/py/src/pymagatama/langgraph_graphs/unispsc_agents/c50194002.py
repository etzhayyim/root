from typing import TypedDict
from langgraph.graph import StateGraph, END

class CherryState(TypedDict):
    batch_id: str
    sugar_content: float
    qc_passed: bool

def validate_brix(state: CherryState):
    if state['sugar_content'] > 20.0:
        return {'qc_passed': True}
    return {'qc_passed': False}

graph = StateGraph(CherryState)
graph.add_node('validate_brix', validate_brix)
graph.set_entry_point('validate_brix')
graph.add_edge('validate_brix', END)
graph = graph.compile()