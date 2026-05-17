from typing import TypedDict
from langgraph.graph import StateGraph, END

class TapeState(TypedDict):
    spec: dict
    validated: bool
    compliance_report: str

def validate_reflectivity(state: TapeState):
    coefficient = state['spec'].get('reflective_coefficient', 0)
    state['validated'] = coefficient > 300
    state['compliance_report'] = 'Pass' if state['validated'] else 'Fail: Low reflectivity'
    return state

def generate_report(state: TapeState):
    print(f'Compliance Status: {state['compliance_report']}')
    return state

graph = StateGraph(TapeState)
graph.add_node('validate', validate_reflectivity)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()