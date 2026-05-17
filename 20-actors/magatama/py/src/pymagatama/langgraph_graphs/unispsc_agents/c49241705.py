from langgraph.graph import StateGraph, END
from typing import TypedDict

class PoolCleanerState(TypedDict):
    model_number: str
    spec_check: bool
    approved: bool

def validate_specs(state: PoolCleanerState):
    # Business logic for verifying pool cleaner technical specifications
    state['spec_check'] = True if state['model_number'] else False
    return 'check_safety'

def check_safety(state: PoolCleanerState):
    # Safety protocols for electrical water equipment
    state['approved'] = state['spec_check']
    return END

graph = StateGraph(PoolCleanerState)
graph.add_node('validate_specs', validate_specs)
graph.add_node('check_safety', check_safety)
graph.set_entry_point('validate_specs')
graph.add_edge('validate_specs', 'check_safety')
graph.add_edge('check_safety', END)
graph = graph.compile()