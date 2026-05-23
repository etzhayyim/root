from typing import TypedDict
from langgraph.graph import StateGraph, END

class PackagingState(TypedDict):
    dispenser_type: str
    max_width: int
    compliance_check: bool

def validate_specs(state: PackagingState):
    state['compliance_check'] = state['max_width'] > 0
    return 'validate_specs'

def finalize_order(state: PackagingState):
    return 'finalize'

graph = StateGraph(PackagingState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
