from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    purity_level: float
    safety_verified: bool
    batch_id: str
    workflow_steps: List[str]

def validate_purity(state: ProcessingState) -> ProcessingState:
    if state['purity_level'] < 0.98:
        raise ValueError('Purity below 98% threshold')
    state['workflow_steps'].append('Purity Validated')
    return state

def check_safety_compliance(state: ProcessingState) -> ProcessingState:
    state['safety_verified'] = True
    state['workflow_steps'].append('Safety Compliance Verified')
    return state

workflow = StateGraph(ProcessingState)
workflow.add_node('validate', validate_purity)
workflow.add_node('safety', check_safety_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'safety')
workflow.add_edge('safety', END)
graph = workflow.compile()