from typing import TypedDict
from langgraph.graph import StateGraph, END

class CharcoalState(TypedDict):
    purity_check: bool
    grade_check: bool
    is_approved: bool

def validate_charcoal_specs(state: CharcoalState):
    # Business logic for charcoal inspection
    state['is_approved'] = state['purity_check'] and state['grade_check']
    return state

graph = StateGraph(CharcoalState)
graph.add_node('validate', validate_charcoal_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()