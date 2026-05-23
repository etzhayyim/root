from typing import TypedDict
from langgraph.graph import StateGraph, END

class KeyAccessoryState(TypedDict):
    material: str
    test_passed: bool
    compliance_report: str

def validate_material(state: KeyAccessoryState):
    state['test_passed'] = state['material'] in ['steel', 'titanium', 'leather']
    return state

def generate_report(state: KeyAccessoryState):
    state['compliance_report'] = 'Certified' if state['test_passed'] else 'Rejected'
    return state

graph = StateGraph(KeyAccessoryState)
graph.add_node('validate', validate_material)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
