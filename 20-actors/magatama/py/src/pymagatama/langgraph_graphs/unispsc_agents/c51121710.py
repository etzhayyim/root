from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    purity: float
    gmp_certified: bool
    approved: bool

def validate_purity(state: DrugState):
    state['approved'] = state['purity'] >= 99.0 and state['gmp_certified']
    return state

workflow = StateGraph(DrugState)
workflow.add_node('validate', validate_purity)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
