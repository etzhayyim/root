from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlaskState(TypedDict):
    capacity_ml: int
    insulation_check: bool
    compliance_verified: bool

def validate_capacity(state: FlaskState):
    return {'insulation_check': state['capacity_ml'] > 0}

def verify_regulations(state: FlaskState):
    return {'compliance_verified': True}

graph = StateGraph(FlaskState)
graph.add_node('validate', validate_capacity)
graph.add_node('compliance', verify_regulations)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
