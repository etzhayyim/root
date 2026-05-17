from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class WorkflowState(TypedDict):
    batch_id: str
    qc_passed: bool
    bead_concentration: float
    errors: List[str]

def validate_concentration(state: WorkflowState):
    passed = 20 <= state['bead_concentration'] <= 30
    return {'qc_passed': passed, 'errors': [] if passed else ['Concentration out of spec']}

def final_approval(state: WorkflowState):
    return {'qc_passed': True}

graph = StateGraph(WorkflowState)
graph.add_node('validate', validate_concentration)
graph.add_node('approve', final_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()