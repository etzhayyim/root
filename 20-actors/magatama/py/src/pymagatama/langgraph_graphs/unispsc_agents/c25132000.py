from langgraph.graph import StateGraph, END
from typing import TypedDict

class AircraftState(TypedDict):
    airworthiness_docs: bool
    compliance_check: str

def validate_docs(state: AircraftState):
    return {'compliance_check': 'PASS' if state['airworthiness_docs'] else 'FAIL'}

def alert_authority(state: AircraftState):
    print('Flagging aircraft purchase for regulatory review.')

graph = StateGraph(AircraftState)
graph.add_node('validate', validate_docs)
graph.add_node('alert', alert_authority)
graph.set_entry_point('validate')
graph.add_edge('validate', 'alert')
graph.add_edge('alert', END)
graph = graph.compile()
