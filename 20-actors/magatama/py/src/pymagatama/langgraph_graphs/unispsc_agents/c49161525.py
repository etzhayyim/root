from typing import TypedDict
from langgraph.graph import StateGraph, END

class SoccerGearState(TypedDict):
    product_id: str
    safety_certification: bool
    impact_test_score: float
    status: str

def validate_safety_standards(state: SoccerGearState):
    state['status'] = 'COMPLIANT' if state['safety_certification'] else 'REJECTED'
    return state

def check_impact_threshold(state: SoccerGearState):
    if state['impact_test_score'] < 0.8:
        state['status'] = 'FAIL_IMPACT_TEST'
    return state

graph = StateGraph(SoccerGearState)
graph.add_node('safety_check', validate_safety_standards)
graph.add_node('impact_analysis', check_impact_threshold)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'impact_analysis')
graph.add_edge('impact_analysis', END)
graph = graph.compile()
