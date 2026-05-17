from typing import TypedDict
from langgraph.graph import StateGraph, END

class SoftballState(TypedDict):
    specs: dict
    approved: bool

def validate_specs(state: SoftballState) -> SoftballState:
    s = state['specs']
    # Check for standard softball specifications
    is_valid = (0.46 <= s.get('cor', 0) <= 0.47) and (178 <= s.get('weight', 0) <= 198)
    return {**state, 'approved': is_valid}

def route_by_validation(state: SoftballState) -> str:
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(SoftballState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_validation, {'approved': END, 'rejected': END})
graph.compile()