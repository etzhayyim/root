from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    commodity_id: str
    purity_check: bool
    safety_clearance: bool
    audit_trail: List[str]

def validate_purity(state: CatalystState) -> CatalystState:
    # Logic to verify purity documentation against COA
    state['purity_check'] = True
    state['audit_trail'].append('Purity validated')
    return state

def check_safety_protocols(state: CatalystState) -> CatalystState:
    # Logic for hazardous material handling compliance
    state['safety_clearance'] = True
    state['audit_trail'].append('Safety protocols cleared')
    return state

graph = StateGraph(CatalystState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_safety', check_safety_protocols)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_safety')
graph.add_edge('check_safety', END)

app = graph.compile()