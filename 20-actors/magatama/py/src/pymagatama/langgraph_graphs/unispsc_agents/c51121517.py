from langgraph.graph import StateGraph, END
from typing import TypedDict
import re

class MexiletineState(TypedDict):
    purity: float
    has_coa: bool
    is_approved: bool

def validate_quality(state: MexiletineState):
    # Regulatory threshold check for Mexiletine Hydrochloride
    if state['purity'] >= 99.0 and state['has_coa']:
        return {'is_approved': True}
    return {'is_approved': False}

graph = StateGraph(MexiletineState)
graph.add_node('validation', validate_quality)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()
