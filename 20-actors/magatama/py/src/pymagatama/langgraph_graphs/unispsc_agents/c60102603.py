from typing import TypedDict
from langgraph.graph import StateGraph, END

class DiceState(TypedDict):
    material: str
    quality_check: bool
    compliance_verified: bool

def validate_material(state: DiceState):
    state['quality_check'] = state['material'] in ['plastic', 'metal', 'resin']
    return state

def verify_compliance(state: DiceState):
    state['compliance_verified'] = True
    return state

graph_builder = StateGraph(DiceState)
graph_builder.add_node('validate', validate_material)
graph_builder.add_node('compliance', verify_compliance)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', 'compliance')
graph_builder.add_edge('compliance', END)
graph = graph_builder.compile()
