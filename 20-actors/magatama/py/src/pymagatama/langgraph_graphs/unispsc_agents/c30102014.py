from typing import TypedDict
from langgraph.graph import StateGraph, END
class LeadFoilState(TypedDict):
    purity: float
    thickness: float
    safety_verified: bool

def validate_purity(state: LeadFoilState):
    state['safety_verified'] = state['purity'] >= 99.9
    return state

def check_thickness(state: LeadFoilState):
    print(f'Validating shield thickness: {state['thickness']} mm')
    return state

graph = StateGraph(LeadFoilState)
graph.add_node('validate_purity', validate_purity)
graph.add_node('check_thickness', check_thickness)
graph.set_entry_point('validate_purity')
graph.add_edge('validate_purity', 'check_thickness')
graph.add_edge('check_thickness', END)
graph = graph.compile()
