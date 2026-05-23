from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PuzzleState(TypedDict):
    piece_count: int
    safety_certs: List[str]
    is_approved: bool

def validate_safety(state: PuzzleState):
    # Ensure safety certifications are present for procurement
    if len(state['safety_certs']) > 0:
        state['is_approved'] = True
    else:
        state['is_approved'] = False
    return state

workflow = StateGraph(PuzzleState)
workflow.add_node('validate_safety', validate_safety)
workflow.set_entry_point('validate_safety')
workflow.add_edge('validate_safety', END)
graph = workflow.compile()
