from langgraph.graph import StateGraph, END
from typing import TypedDict

class DentalState(TypedDict):
    material_name: str
    iso_compliant: bool
    sterility_check: bool

def validate_biocompatibility(state: DentalState):
    state['iso_compliant'] = True
    return 'check_sterility'

def check_sterility(state: DentalState):
    state['sterility_check'] = True
    return END

graph = StateGraph(DentalState)
graph.add_node('validate', validate_biocompatibility)
graph.add_node('check_sterility', check_sterility)
graph.add_edge('validate', 'check_sterility')
graph.add_edge('check_sterility', END)
graph.set_entry_point('validate')
graph = graph.compile()
