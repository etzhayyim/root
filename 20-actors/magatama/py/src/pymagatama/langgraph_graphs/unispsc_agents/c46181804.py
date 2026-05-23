from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GoggleSpecs(TypedDict):
    material: str
    standard_compliance: str
    is_approved: bool

def validate_safety_standards(state: GoggleSpecs):
    required = ['ANSI Z87.1', 'EN 166']
    state['is_approved'] = state['standard_compliance'] in required
    return state

def quality_control_router(state: GoggleSpecs):
    return 'pass' if state['is_approved'] else 'fail'

graph = StateGraph(GoggleSpecs)
graph.add_node('validate', validate_safety_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
