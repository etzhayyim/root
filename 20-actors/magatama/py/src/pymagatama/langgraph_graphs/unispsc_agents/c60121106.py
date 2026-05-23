from langgraph.graph import StateGraph, END
from typing import TypedDict

class PaperState(TypedDict):
    weight_gsm: int
    surface_type: str
    is_acid_free: bool
    approved: bool

def validate_paper_spec(state: PaperState):
    if state['weight_gsm'] >= 200 and state['is_acid_free']:
        state['approved'] = True
    else:
        state['approved'] = False
    return state

graph = StateGraph(PaperState)
graph.add_node("validate", validate_paper_spec)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
