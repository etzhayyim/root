from langgraph.graph import StateGraph, END
from typing import TypedDict
class BalloonState(TypedDict):
    airworthiness_docs: dict
    component_check: bool
    is_cleared: bool
def validate_certification(state: BalloonState):
    state['component_check'] = 'Airworthiness' in state['airworthiness_docs']
    return {'component_check': state['component_check']}
def finalize_approval(state: BalloonState):
    state['is_cleared'] = state['component_check']
    return {'is_cleared': state['is_cleared']}
graph = StateGraph(BalloonState)
graph.add_node('validate', validate_certification)
graph.add_node('approve', finalize_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
