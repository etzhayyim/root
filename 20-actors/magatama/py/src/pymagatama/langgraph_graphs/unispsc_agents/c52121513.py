from typing import TypedDict
from langgraph.graph import StateGraph, END

class BedspreadState(TypedDict):
    specs: dict
    is_compliant: bool

def validate_specs(state: BedspreadState):
    required = ['material', 'dimensions', 'flammability']
    compliant = all(k in state['specs'] for k in required)
    return {'is_compliant': compliant}

def route_by_compliance(state: BedspreadState):
    return 'process' if state['is_compliant'] else END

graph = StateGraph(BedspreadState)
graph.add_node('validate', validate_specs)
graph.add_node('process', lambda x: x)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_compliance)
graph.add_edge('process', END)
graph = graph.compile()