from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LeadBeamState(TypedDict):
    specs: dict
    approved: bool
    safety_check: bool

def validate_density(state: LeadBeamState):
    density = state['specs'].get('density', 0)
    return {'safety_check': density >= 11.34}

def final_approval(state: LeadBeamState):
    return {'approved': state['safety_check'] == True}

graph = StateGraph(LeadBeamState)
graph.add_node('validate', validate_density)
graph.add_node('approve', final_approval)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()