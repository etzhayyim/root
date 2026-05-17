from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    spec_data: dict
    validation_errors: List[str]
    is_approved: bool

def validate_acoustic_specs(state: ProcessingState):
    errors = []
    if state['spec_data'].get('stc_rating', 0) < 30:
        errors.append('Insufficient STC rating for noise control')
    return {**state, 'validation_errors': errors}

def final_approval(state: ProcessingState):
    return {**state, 'is_approved': len(state['validation_errors']) == 0}

graph = StateGraph(ProcessingState)
graph.add_node('validate', validate_acoustic_specs)
graph.add_node('approve', final_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()