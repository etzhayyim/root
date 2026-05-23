from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PharmState(TypedDict):
    api_name: str
    purity_level: float
    gmp_valid: bool
    approved: bool

def validate_quality(state: PharmState):
    state['approved'] = state['purity_level'] >= 99.0 and state['gmp_valid']
    return state

workflow = StateGraph(PharmState)
workflow.add_node('quality_check', validate_quality)
workflow.set_entry_point('quality_check')
workflow.add_edge('quality_check', END)
graph = workflow.compile()
