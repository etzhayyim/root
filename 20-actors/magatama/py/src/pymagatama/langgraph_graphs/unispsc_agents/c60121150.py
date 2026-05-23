from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class SugarPaperState(TypedDict):
    spec_data: dict
    validation_results: List[str]
    approved: bool

def validate_food_safety(state: SugarPaperState):
    cert = state['spec_data'].get('food_grade_certification')
    if cert:
        state['validation_results'].append('Certification verified.')
    else:
        state['validation_results'].append('Missing certification.')
    return state

def check_expiry(state: SugarPaperState):
    expiry = state['spec_data'].get('expiry_date')
    if expiry:
        state['approved'] = True
    return state

graph = StateGraph(SugarPaperState)
graph.add_node('safety_check', validate_food_safety)
graph.add_node('expiry_check', check_expiry)
graph.add_edge('safety_check', 'expiry_check')
graph.add_edge('expiry_check', END)
graph.set_entry_point('safety_check')
