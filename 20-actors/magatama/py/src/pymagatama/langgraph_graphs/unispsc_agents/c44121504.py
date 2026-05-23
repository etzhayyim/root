from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EnvelopeState(TypedDict):
    order_id: str
    specifications: dict
    approved: bool
    validation_log: List[str]

def validate_specs(state: EnvelopeState):
    specs = state['specifications']
    logs = []
    if specs.get('paper_weight_gsm', 0) < 80:
        logs.append('Insufficient paper weight')
    return {'validation_log': logs, 'approved': len(logs) == 0}

def route_by_validation(state: EnvelopeState):
    return 'approved' if state['approved'] else 'rejected'

graph = StateGraph(EnvelopeState)
graph.add_node('validate', validate_specs)
graph.add_edge('__start__', 'validate')
graph.add_conditional_edges('validate', route_by_validation, {'approved': END, 'rejected': END})
graph = graph.compile()
