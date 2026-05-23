from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FiberTestState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: FiberTestState):
    required = ['wavelength', 'power_dbm']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_report': 'Passed' if valid else 'Missing specs'}

def finalize_procurement(state: FiberTestState):
    return {'compliance_report': 'Ready for supplier issuance'}

graph = StateGraph(FiberTestState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
