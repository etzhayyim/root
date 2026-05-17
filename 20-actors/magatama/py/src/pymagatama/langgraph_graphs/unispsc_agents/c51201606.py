from typing import TypedDict
from langgraph.graph import StateGraph, END

class BioSpecimenState(TypedDict):
    biosafety_level: int
    storage_temp: float
    compliance_cleared: bool

def validate_bsl(state: BioSpecimenState):
    state['compliance_cleared'] = state['biosafety_level'] >= 2
    return state

def route_procurement(state: BioSpecimenState):
    return 'process' if state['compliance_cleared'] else 'reject'

graph = StateGraph(BioSpecimenState)
graph.add_node('validate', validate_bsl)
graph.add_edge('validate', 'process')
graph.set_entry_point('validate')
graph.add_edge('process', END)
graph = graph.compile()