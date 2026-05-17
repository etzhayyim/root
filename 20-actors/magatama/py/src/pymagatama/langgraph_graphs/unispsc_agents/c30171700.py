from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class GlassState(TypedDict):
    specs: dict
    validation_reports: List[str]
    approved: bool

def validate_glass_safety(state: GlassState):
    thickness = state['specs'].get('thickness', 0)
    if thickness < 3:
        state['validation_reports'].append('Safety Alert: Glass too thin for structural use')
    return {'validation_reports': state['validation_reports']}

def approval_check(state: GlassState):
    return 'approved' if len(state['validation_reports']) == 0 else 'rejected'

graph = StateGraph(GlassState)
graph.add_node('safety_check', validate_glass_safety)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', END)