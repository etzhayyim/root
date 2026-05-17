from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class KitchenUnitState(TypedDict):
    specs: dict
    validation_passed: bool
    compliance_report: List[str]

def validate_specs(state: KitchenUnitState):
    errors = []
    if not state['specs'].get('sanitation_certified'):
        errors.append('Missing sanitation certification')
    return {'validation_passed': len(errors) == 0, 'compliance_report': errors}

def finalize_order(state: KitchenUnitState):
    return {'compliance_report': ['Order ready for procurement approval']}

graph = StateGraph(KitchenUnitState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()