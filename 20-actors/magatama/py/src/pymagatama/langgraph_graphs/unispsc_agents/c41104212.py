from typing import TypedDict
from langgraph.graph import StateGraph, END

class FilterState(TypedDict):
    specs: dict
    validated: bool
    compliance_report: str

def validate_specs(state: FilterState):
    required = ['micron', 'flow_rate', 'certification']
    valid = all(k in state['specs'] for k in required)
    return {'validated': valid, 'compliance_report': 'Passed' if valid else 'Missing fields'}

def check_compliance(state: FilterState):
    if state.get('validated'):
        return 'final'
    return 'error'

graph = StateGraph(FilterState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', check_compliance, {'final': END, 'error': END})
graph = graph.compile()
