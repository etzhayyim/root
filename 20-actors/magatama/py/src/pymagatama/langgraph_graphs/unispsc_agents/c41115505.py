from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SoundTestState(TypedDict):
    room_specs: dict
    validation_passed: bool
    compliance_report: str

def validate_acoustic_specs(state: SoundTestState):
    specs = state['room_specs']
    passed = specs.get('background_noise', 30) <= 20 and specs.get('isolation_db', 0) >= 50
    return {'validation_passed': passed, 'compliance_report': 'Success' if passed else 'Failed acoustic threshold'}

def generate_report(state: SoundTestState):
    return {'compliance_report': f'Room certified for research with status: {state['validation_passed']}'}

graph = StateGraph(SoundTestState)
graph.add_node('validate', validate_acoustic_specs)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
