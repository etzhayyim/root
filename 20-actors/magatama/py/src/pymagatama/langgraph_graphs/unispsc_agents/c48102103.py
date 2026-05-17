from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class DisplayCaseState(TypedDict):
    spec_data: dict
    validation_passed: bool
    log: List[str]

def validate_cooling(state: DisplayCaseState):
    temp = state['spec_data'].get('temp', 0)
    passed = -18 <= temp <= 8
    return {'validation_passed': passed, 'log': [f'Temp validated: {passed}']}

def check_compliance(state: DisplayCaseState):
    cert = state['spec_data'].get('cert', '')
    passed = bool(cert) and state.get('validation_passed', False)
    return {'validation_passed': passed, 'log': state.get('log', []) + ['Compliance checked']}

graph = StateGraph(DisplayCaseState)
graph.add_node('validate', validate_cooling)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()