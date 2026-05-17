from typing import TypedDict, Annotated, List, Union
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class MineralState(TypedDict):
    purity: float
    safety_compliance: bool
    refining_stage: str
    logs: Annotated[List[str], add_messages]

def validate_purity(state: MineralState) -> MineralState:
    if state['purity'] < 0.98:
        state['logs'].append('Validation Failed: Low Purity')
    else:
        state['logs'].append('Validation Passed: Standard Purity')
    return state

def check_compliance(state: MineralState) -> MineralState:
    state['safety_compliance'] = True
    state['logs'].append('Compliance Checked: Regulatory Standard Met')
    return state

graph = StateGraph(MineralState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()