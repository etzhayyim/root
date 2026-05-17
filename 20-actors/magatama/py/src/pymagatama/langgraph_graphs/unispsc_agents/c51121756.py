from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class MetyrosineState(TypedDict):
    batch_id: str
    purity_level: float
    quality_check_passed: bool
    steps: List[str]

def validate_purity(state: MetyrosineState) -> MetyrosineState:
    state['quality_check_passed'] = state['purity_level'] >= 99.5
    state['steps'].append('Purity Validation')
    return state

def regulatory_check(state: MetyrosineState) -> MetyrosineState:
    if state['quality_check_passed']:
        state['steps'].append('Regulatory Compliance Audit')
    return state

graph = StateGraph(MetyrosineState)
graph.add_node('validate', validate_purity)
graph.add_node('regulatory', regulatory_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'regulatory')
graph.add_edge('regulatory', END)
graph = graph.compile()