from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcureState(TypedDict):
    drug_name: str
    quality_docs: List[str]
    storage_temp: float
    validation_pass: bool

def validate_pharma_spec(state: ProcureState):
    state['validation_pass'] = len(state['quality_docs']) >= 2 and state['storage_temp'] <= 5.0
    return state

workflow = StateGraph(ProcureState)
workflow.add_node('validate', validate_pharma_spec)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()