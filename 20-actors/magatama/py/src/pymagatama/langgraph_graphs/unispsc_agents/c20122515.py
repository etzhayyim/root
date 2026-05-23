from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_id: str
    specs: dict
    validation_results: List[str]
    is_approved: bool

def validate_specs(state: BearingState) -> BearingState:
    results = []
    if state['specs'].get('load_rating_kn', 0) <= 0:
        results.append('Invalid load rating')
    return {**state, 'validation_results': results, 'is_approved': len(results) == 0}

workflow = StateGraph(BearingState)
workflow.add_node('validate', validate_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
