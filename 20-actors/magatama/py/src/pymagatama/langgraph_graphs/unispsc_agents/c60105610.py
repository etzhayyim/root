from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrainingMaterialState(TypedDict):
    material_type: str
    content_verified: bool
    compliance_check: bool

def validate_material(state: TrainingMaterialState):
    state['content_verified'] = True
    return 'valid' if state['content_verified'] else 'invalid'

def check_compliance(state: TrainingMaterialState):
    state['compliance_check'] = True
    return state

graph = StateGraph(TrainingMaterialState)
graph.add_node('validate', validate_material)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)

app = graph.compile()
