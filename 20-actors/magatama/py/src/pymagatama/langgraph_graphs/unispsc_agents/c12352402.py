from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class SolventState(TypedDict):
    purity: float
    safety_check_passed: bool
    log: List[str]

def validate_purity(state: SolventState) -> SolventState:
    if state['purity'] >= 0.99:
        state['log'].append('Purity validated at >= 99%')
        state['safety_check_passed'] = True
    else:
        state['log'].append('Purity check failed')
        state['safety_check_passed'] = False
    return state

def route_by_safety(state: SolventState) -> str:
    return 'process' if state['safety_check_passed'] else 'reject'

graph = StateGraph(SolventState)
graph.add_node('validate', validate_purity)
graph.add_node('process', lambda x: x)
graph.add_node('reject', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_safety)
graph.add_edge('process', END)
graph.add_edge('reject', END)
graph = graph.compile()
