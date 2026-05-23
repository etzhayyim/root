from typing import TypedDict
from langgraph.graph import StateGraph, END

class TryptophanState(TypedDict):
    purity: float
    co_a_provided: bool
    compliant: bool

def validate_quality(state: TryptophanState):
    state['compliant'] = state['purity'] >= 99.0 and state['co_a_provided']
    return state

workflow = StateGraph(TryptophanState)
workflow.add_node('validation', validate_quality)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()
