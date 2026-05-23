from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class ProcessingState(TypedDict):
    material_id: str
    purity: float
    process_steps: Annotated[list[str], operator.add]
    is_compliant: bool

def validate_chemical_purity(state: ProcessingState) -> ProcessingState:
    state['is_compliant'] = state['purity'] >= 99.5
    state['process_steps'].append('Purity Validation Complete')
    return state

def execute_refining_workflow(state: ProcessingState) -> ProcessingState:
    if state['is_compliant']:
        state['process_steps'].append('Refining Step Applied')
    return state

builder = StateGraph(ProcessingState)
builder.add_node('validate', validate_chemical_purity)
builder.add_node('refine', execute_refining_workflow)
builder.add_edge('validate', 'refine')
builder.add_edge('refine', END)
builder.set_entry_point('validate')
graph = builder.compile()
