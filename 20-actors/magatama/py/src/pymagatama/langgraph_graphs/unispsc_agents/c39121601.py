from typing import TypedDict
from langgraph.graph import StateGraph, END

class CircuitBreakerState(TypedDict):
    specs: dict
    validation: bool
    compliant: bool

def validate_specs(state: CircuitBreakerState):
    s = state['specs']
    valid = all([s.get('voltage'), s.get('capacity'), s.get('poles')])
    return {'validation': valid}

def check_compliance(state: CircuitBreakerState):
    compliant = state['validation'] and 'UL' in state['specs'].get('cert', '')
    return {'compliant': compliant}

graph = StateGraph(CircuitBreakerState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()