from typing import TypedDict, Annotated, List, Dict, Any
from langgraph.graph import StateGraph, END

class CatalystState(TypedDict):
    catalyst_id: str
    purity: float
    activity_score: float
    validation_passed: bool
    log: List[str]

def validate_purity(state: CatalystState) -> CatalystState:
    state['validation_passed'] = state['purity'] >= 0.99
    state['log'].append(f'Purity check: {state["purity"]} - Status: {state["validation_passed"]}')
    return state

def evaluate_catalyst(state: CatalystState) -> CatalystState:
    if state['validation_passed'] and state['activity_score'] > 0.8:
        state['log'].append('Catalyst meets high-activity industrial specs.')
    else:
        state['log'].append('Catalyst rejected due to insufficient specs.')
    return state

def build_graph():
    workflow = StateGraph(CatalystState)
    workflow.add_node('validate', validate_purity)
    workflow.add_node('evaluate', evaluate_catalyst)
    workflow.add_edge('validate', 'evaluate')
    workflow.add_edge('evaluate', END)
    workflow.set_entry_point('validate')
    return workflow.compile()

graph = build_graph()