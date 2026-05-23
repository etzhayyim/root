from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class PaperboardState(TypedDict):
    material_id: str
    thickness: float
    acid_free: bool
    is_approved: bool

def validate_paper_spec(state: PaperboardState) -> PaperboardState:
    # Business logic for paperboard quality validation
    state['is_approved'] = state['thickness'] >= 0.5 and state['acid_free']
    return state

def archival_routing(state: PaperboardState) -> str:
    return 'process' if state['is_approved'] else 'reject'

workflow = StateGraph(PaperboardState)
workflow.add_node('validate', validate_paper_spec)
workflow.add_edge('validate', END)
workflow.set_entry_point('validate')

graph = workflow.compile()
