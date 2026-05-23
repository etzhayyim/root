from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    commodity_code: str
    purity_level: float
    origin_country: str
    compliance_passed: bool
    inspection_steps: List[str]

def validate_purity(state: MineralState):
    passed = state['purity_level'] >= 99.5
    return {'compliance_passed': passed, 'inspection_steps': ['purity_check']}

def check_compliance(state: MineralState):
    if state['origin_country'] in ['restricted_list']:
        return {'compliance_passed': False}
    return {'inspection_steps': state['inspection_steps'] + ['compliance_check']}

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
