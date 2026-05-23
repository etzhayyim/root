from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class SpillDeckState(TypedDict):
    specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_specs(state: SpillDeckState):
    errors = []
    if state['specs'].get('sump_capacity', 0) <= 0:
        errors.append('Invalid sump capacity')
    return {'validation_errors': errors, 'is_compliant': len(errors) == 0}

def route_by_compliance(state: SpillDeckState):
    return 'compliant' if state['is_compliant'] else 'manual_review'

graph = StateGraph(SpillDeckState)
graph.add_node('validate', validate_specs)
graph.add_node('compliant', lambda x: x)
graph.add_node('manual_review', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('compliant', END)
graph.add_edge('manual_review', END)
graph = graph.compile()
