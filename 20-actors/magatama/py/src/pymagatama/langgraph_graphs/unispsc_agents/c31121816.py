from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class CastingState(TypedDict):
    specifications: dict
    validation_checks: List[str]
    approved: bool

def validate_purity(state: CastingState):
    purity = state['specifications'].get('purity_percentage', 0)
    is_valid = purity >= 99.9
    return {'validation_checks': state['validation_checks'] + [f'Purity check: {is_valid}'], 'approved': is_valid}

def structural_integrity_check(state: CastingState):
    return {'validation_checks': state['validation_checks'] + ['NDT scan completed'], 'approved': state['approved']}

graph = StateGraph(CastingState)
graph.add_node('purity_check', validate_purity)
graph.add_node('structural_check', structural_integrity_check)
graph.set_entry_point('purity_check')
graph.add_edge('purity_check', 'structural_check')
graph.add_edge('structural_check', END)
graph = graph.compile()