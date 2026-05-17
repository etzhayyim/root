from typing import TypedDict
from langgraph.graph import StateGraph, END
class FilterState(TypedDict):
    spec_data: dict
    validation_results: list
    is_compliant: bool
def validate_efficiency(state: FilterState):
    eff = state['spec_data'].get('bfe', 0)
    return {'validation_results': ['BFE > 99.9%'] if eff >= 99.9 else ['BFE failed']}
def check_compliance(state: FilterState):
    is_compliant = 'BFE failed' not in state['validation_results']
    return {'is_compliant': is_compliant}
workflow = StateGraph(FilterState)
workflow.add_node('validate', validate_efficiency)
workflow.add_node('compliance', check_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'compliance')
workflow.add_edge('compliance', END)
graph = workflow.compile()