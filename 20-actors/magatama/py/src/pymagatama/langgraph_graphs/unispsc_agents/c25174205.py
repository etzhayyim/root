from typing import TypedDict, List
from langgraph.graph import StateGraph

class TieRodState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: TieRodState):
    required = ['material', 'tensile_strength']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_report': 'Passed' if valid else 'Failed'}

def approval_node(state: TieRodState):
    return {'compliance_report': 'Approved for procurement'}

graph = StateGraph(TieRodState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_node)
graph.add_edge('validate', 'approve')
graph.set_entry_point('validate')
graph.set_finish_point('approve')
graph = graph.compile()
