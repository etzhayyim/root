from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ExtractionState(TypedDict):
    commodity_code: str
    purity_level: float
    safety_clearance: bool
    process_steps: List[str]

def validate_reagent(state: ExtractionState) -> ExtractionState:
    if state.get('purity_level', 0) < 95.0:
        state['process_steps'].append('Rejected: Purity below threshold')
    else:
        state['process_steps'].append('Validated: Purity sufficient')
    return state

def execute_safety_check(state: ExtractionState) -> ExtractionState:
    state['safety_clearance'] = True
    state['process_steps'].append('Safety protocols initialized')
    return state

def compile_graph():
    workflow = StateGraph(ExtractionState)
    workflow.add_node('validate', validate_reagent)
    workflow.add_node('safety', execute_safety_check)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', 'safety')
    workflow.add_edge('safety', END)
    return workflow.compile()

graph = compile_graph()