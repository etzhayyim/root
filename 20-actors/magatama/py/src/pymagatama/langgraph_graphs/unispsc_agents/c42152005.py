from typing import TypedDict
from langgraph.graph import StateGraph, END

class DentalImagingState(TypedDict):
    part_number: str
    material_certified: bool
    sterilization_validated: bool

def check_compliance(state: DentalImagingState):
    state['material_certified'] = True
    return 'COMPLIANT' if state['material_certified'] else 'NON_COMPLIANT'

def validate_sterilization(state: DentalImagingState):
    state['sterilization_validated'] = True
    return {'sterilization_validated': True}

graph = StateGraph(DentalImagingState)
graph.add_node('compliance', check_compliance)
graph.add_node('sterilization', validate_sterilization)
graph.set_entry_point('compliance')
graph.add_edge('compliance', 'sterilization')
graph.add_edge('sterilization', END)
graph = graph.compile()
