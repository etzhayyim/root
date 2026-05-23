from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlycerineState(TypedDict):
    purity: float
    grade: str
    is_compliant: bool

def validate_purity(state: GlycerineState):
    state['is_compliant'] = state['purity'] >= 99.5
    return state

workflow = StateGraph(GlycerineState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
