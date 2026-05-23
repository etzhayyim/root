from typing import TypedDict, List
from langgraph.graph import StateGraph, END
class AircraftState(TypedDict):
    serial_number: str
    compliance_docs: List[str]
    approved: bool

def validate_compliance(state: AircraftState):
    state['approved'] = len(state['compliance_docs']) >= 3
    return state

def check_export_control(state: AircraftState):
    print('Checking export controls for military aircraft...')
    return state

graph = StateGraph(AircraftState)
graph.add_node('validate', validate_compliance)
graph.add_node('export', check_export_control)
graph.add_edge('validate', 'export')
graph.add_edge('export', END)
graph.set_entry_point('validate')
graph = graph.compile()
