from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class NystatinState(TypedDict):
    purity: float
    gmp_certified: bool
    compliance_report: str
    approved: bool

def validate_quality(state: NystatinState):
    if state['purity'] >= 99.9 and state['gmp_certified']:
        return {'approved': True}
    return {'approved': False}

def process_procurement(state: NystatinState):
    print(f"Processing Nystatin procurement: Status={state['approved']}")
    return state

graph = StateGraph(NystatinState)
graph.add_node("validate", validate_quality)
graph.add_node("process", process_procurement)
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph.set_entry_point("validate")
compiled_graph = graph.compile()