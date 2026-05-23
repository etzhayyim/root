from typing import TypedDict
from langgraph.graph import StateGraph, END

class ShoeState(TypedDict):
    spec_data: dict
    validated: bool
    compliance_report: str

def validate_specs(state: ShoeState):
    required = ['material', 'size', 'slip_rating']
    valid = all(k in state['spec_data'] for k in required)
    return {'validated': valid, 'compliance_report': 'Passed' if valid else 'Incomplete'}

def finalize_procurement(state: ShoeState):
    return {'compliance_report': 'Procurement order ready for authorization.'}

graph = StateGraph(ShoeState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_procurement)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
