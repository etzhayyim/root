from typing import TypedDict
from langgraph.graph import StateGraph, END

class GlasswareState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_log: list

def validate_glass_standards(state: GlasswareState):
    report = []
    compliant = True
    if state['specs'].get('lead_content', 0) > 0.05:
        report.append('Lead content exceeds safety threshold')
        compliant = False
    return {'is_compliant': compliant, 'validation_log': report}

def approval_check(state: GlasswareState):
    return 'approved' if state['is_compliant'] else 'rejected'

graph = StateGraph(GlasswareState)
graph.add_node('validate', validate_glass_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', END)