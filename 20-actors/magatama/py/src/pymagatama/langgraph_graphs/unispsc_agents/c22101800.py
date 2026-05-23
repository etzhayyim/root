from typing import TypedDict
from langgraph.graph import StateGraph, END

class OpticalState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_optics(state: OpticalState):
    wavelength = state['specs'].get('wavelength')
    is_valid = 300 < wavelength < 2000 if wavelength else False
    return {'validated': is_valid, 'compliance_report': 'Validated' if is_valid else 'Failed'}

graph = StateGraph(OpticalState)
graph.add_node('validate', validate_optics)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
