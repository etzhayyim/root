from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    purity_level: float
    safety_compliance: bool
    is_approved: bool

def validate_purity(state: CatalystState):
    is_valid = state['purity_level'] >= 99.9
    return {'is_approved': is_valid}

def check_safety(state: CatalystState):
    # Simulate regulatory check
    return {'safety_compliance': True}

workflow = StateGraph(CatalystState)
workflow.add_node('purity_check', validate_purity)
workflow.add_node('safety_check', check_safety)
workflow.set_entry_point('purity_check')
workflow.add_edge('purity_check', 'safety_check')
workflow.add_edge('safety_check', END)
graph = workflow.compile()
