from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BoltState(TypedDict):
    specs: dict
    validated: bool
    error: List[str]

def validate_specs(state: BoltState):
    required = ['material', 'thread', 'tensile_strength']
    missing = [f for f in required if f not in state['specs']]
    return {'validated': len(missing) == 0, 'error': missing}

def check_compliance(state: BoltState):
    return {'validated': state['validated'] and state['specs'].get('iso_compliant', False)}

graph = StateGraph(BoltState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
