from typing import TypedDict
from langgraph.graph import StateGraph, END

class IndicatorState(TypedDict):
    part_number: str
    spec_compliance: bool
    approved: bool

def validate_specs(state: IndicatorState):
    # Business logic for validation: check if part complies with IP standards
    state['spec_compliance'] = True if state['part_number'].startswith('IND') else False
    return {'spec_compliance': state['spec_compliance']}

def approval_check(state: IndicatorState):
    state['approved'] = state['spec_compliance']
    return {'approved': state['approved']}

graph = StateGraph(IndicatorState)
graph.add_node('validate', validate_specs)
graph.add_node('approve', approval_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()
