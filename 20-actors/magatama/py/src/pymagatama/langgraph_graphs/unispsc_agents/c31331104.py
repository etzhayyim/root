from typing import TypedDict
from langgraph.graph import StateGraph, END

class InconelState(TypedDict):
    part_id: str
    bonding_method: str
    is_certified: bool
    validation_score: float

def validate_specs(state: InconelState):
    state['validation_score'] = 1.0 if state['is_certified'] else 0.0
    return {'validation_score': state['validation_score']}

def check_compliance(state: InconelState):
    return 'compliant' if state['validation_score'] >= 1.0 else 'rejected'

graph = StateGraph(InconelState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
app = graph.compile()
