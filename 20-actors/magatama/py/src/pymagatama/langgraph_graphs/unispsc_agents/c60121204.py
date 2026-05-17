from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class PaintWorkflowState(TypedDict):
    product_id: str
    safety_certs: List[str]
    washability_grade: int
    approved: bool

def validate_safety(state: PaintWorkflowState):
    # Validate against ASTM D-4236 standards
    state['approved'] = 'ASTM_D4236' in state['safety_certs']
    return state

def check_quality(state: PaintWorkflowState):
    # Fine-grained check of washability index
    if state.get('washability_grade', 0) > 8:
        state['approved'] = True
    return state

graph = StateGraph(PaintWorkflowState)
graph.add_node('safety_check', validate_safety)
graph.add_node('quality_check', check_quality)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'quality_check')
graph.add_edge('quality_check', END)
graph = graph.compile()