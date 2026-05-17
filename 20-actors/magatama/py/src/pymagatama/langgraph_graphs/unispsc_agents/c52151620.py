from typing import TypedDict
from langgraph.graph import StateGraph, END

class SifterProcurementState(TypedDict):
    sifter_spec: dict
    validation_passed: bool

# Workflow nodes
def validate_material(state: SifterProcurementState):
    material = state['sifter_spec'].get('material')
    state['validation_passed'] = material in ['Stainless Steel', 'Food-grade Plastic']
    return state

def check_compliance(state: SifterProcurementState):
    return state

graph = StateGraph(SifterProcurementState)
graph.add_node('validate_material', validate_material)
graph.add_node('check_compliance', check_compliance)
graph.set_entry_point('validate_material')
graph.add_edge('validate_material', 'check_compliance')
graph.add_edge('check_compliance', END)
graph = graph.compile()