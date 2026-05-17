from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class OfficePaperState(TypedDict):
    paper_id: str
    spec_requirements: dict
    validation_passed: bool
    inspection_logs: List[str]

def validate_paper_spec(state: OfficePaperState) -> OfficePaperState:
    specs = state.get('spec_requirements', {})
    # Specialized logic for paper grade validation
    passed = specs.get('brightness_percentage', 0) >= 80
    state['validation_passed'] = passed
    state['inspection_logs'].append(f'Brightness check passed: {passed}')
    return state

def quality_control_node(state: OfficePaperState) -> OfficePaperState:
    state['inspection_logs'].append('Performing density and moisture content check.')
    return state

graph = StateGraph(OfficePaperState)
graph.add_node('validate', validate_paper_spec)
graph.add_node('qc', quality_control_node)
graph.set_entry_point('validate')
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph = graph.compile()