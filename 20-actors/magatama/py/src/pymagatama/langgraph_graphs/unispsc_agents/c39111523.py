from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LightingState(TypedDict):
    specs: dict
    is_compliant: bool
    validation_issues: List[str]

def validate_specs(state: LightingState):
    issues = []
    if 'IP_rating' not in state['specs']: issues.append('Missing IP rating')
    if 'voltage_range' not in state['specs']: issues.append('Missing voltage range')
    return {'is_compliant': len(issues) == 0, 'validation_issues': issues}

graph = StateGraph(LightingState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
