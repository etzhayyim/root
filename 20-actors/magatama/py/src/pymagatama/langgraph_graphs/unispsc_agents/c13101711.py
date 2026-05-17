from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    raw_data: dict
    analysis_results: dict
    compliance_flags: List[str]
    approved: bool

def validate_purity(state: MineralState) -> MineralState:
    purity = state['raw_data'].get('purity', 0)
    state['analysis_results']['purity_ok'] = purity >= 95.0
    return state

def check_compliance(state: MineralState) -> MineralState:
    if state['analysis_results'].get('purity_ok'):
        state['compliance_flags'].append('QUALITY_PASSED')
        state['approved'] = True
    else:
        state['compliance_flags'].append('QUALITY_FAILED')
        state['approved'] = False
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()