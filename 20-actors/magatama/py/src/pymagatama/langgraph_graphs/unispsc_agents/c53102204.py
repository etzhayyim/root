from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ClothingState(TypedDict):
    spec_data: dict
    is_compliant: bool
    validation_report: List[str]

def validate_quality(state: ClothingState):
    report = []
    if 'dye_safety' not in state['spec_data']: report.append('Missing dye safety test')
    return {'is_compliant': len(report) == 0, 'validation_report': report}

def approval_check(state: ClothingState):
    return 'approved' if state['is_compliant'] else 'manual_review'

graph = StateGraph(ClothingState)
graph.add_node('validate', validate_quality)
graph.add_edge('validate', END)
graph.set_entry_point('validate')