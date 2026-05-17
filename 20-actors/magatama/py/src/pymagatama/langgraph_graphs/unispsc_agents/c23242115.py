from typing import TypedDict
from langgraph.graph import StateGraph, END

class TailstockState(TypedDict):
    specs: dict
    validated: bool
    compliance_risk: str

def validate_specs(state: TailstockState):
    required = ['center-height', 'morse-taper-size']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_risk': 'low' if valid else 'high'}

def check_compliance(state: TailstockState):
    return {'compliance_risk': 'export-review' if state['specs'].get('precision') == 'high' else 'approved'}

graph = StateGraph(TailstockState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()