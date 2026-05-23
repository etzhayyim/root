from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InfantApparelState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_log: List[str]

def validate_safety_certs(state: InfantApparelState):
    certs = state['spec_data'].get('certifications', [])
    valid = 'OEKO-TEX' in certs or 'CPSIA' in certs
    state['is_compliant'] = valid
    state['validation_log'].append(f'Safety compliance status: {valid}')
    return state

def finalize_procurement(state: InfantApparelState):
    state['validation_log'].append('Procurement workflow finalized for infant apparel.')
    return state

graph = StateGraph(InfantApparelState)
graph.add_node('validate', validate_safety_certs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
