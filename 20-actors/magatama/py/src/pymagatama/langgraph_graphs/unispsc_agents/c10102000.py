from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    commodity_code: str
    purity: float
    origin: str
    compliance_cleared: bool
    workflow_log: List[str]

def validate_purity(state: MineralState) -> MineralState:
    if state['purity'] >= 99.9:
        state['workflow_log'].append('Purity check passed')
        state['compliance_cleared'] = True
    else:
        state['workflow_log'].append('Purity below industry standard')
        state['compliance_cleared'] = False
    return state

def check_compliance(state: MineralState) -> MineralState:
    if state['origin'] != 'restricted':
        state['workflow_log'].append('Origin compliance confirmed')
    else:
        state['compliance_cleared'] = False
        state['workflow_log'].append('Origin restricted')
    return state

graph = StateGraph(MineralState)
graph.add_node('validate', validate_purity)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
