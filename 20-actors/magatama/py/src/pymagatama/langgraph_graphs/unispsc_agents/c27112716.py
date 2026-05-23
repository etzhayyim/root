from typing import TypedDict
from langgraph.graph import StateGraph, END

class NailGunState(TypedDict):
    model_id: str
    pressure_rating: int
    safety_check_passed: bool

def validate_specs(state: NailGunState):
    if state['pressure_rating'] > 120:
        return {'safety_check_passed': False}
    return {'safety_check_passed': True}

def final_approval(state: NailGunState):
    return 'APPROVED' if state['safety_check_passed'] else 'REJECTED'

graph = StateGraph(NailGunState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', final_approval)
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph.set_entry_point('validate')
graph = graph.compile()
