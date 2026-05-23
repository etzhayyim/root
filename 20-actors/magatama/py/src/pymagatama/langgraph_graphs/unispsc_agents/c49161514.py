from typing import TypedDict
from langgraph.graph import StateGraph, END

class HockeyBallState(TypedDict):
    material: str
    weight: float
    certification: str
    is_approved: bool

def validate_ball_specs(state: HockeyBallState):
    # Basic quality control validation logic
    valid_weight = 156.0 <= state['weight'] <= 163.0
    state['is_approved'] = valid_weight and state['certification'] == 'FIH'
    return state

workflow = StateGraph(HockeyBallState)
workflow.add_node('qualification', validate_ball_specs)
workflow.set_entry_point('qualification')
workflow.add_edge('qualification', END)
graph = workflow.compile()
