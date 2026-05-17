from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlooringState(TypedDict):
    specs: dict
    validation_passed: bool
    log: list

def validate_material(state: FlooringState):
    hardness = state['specs'].get('mohs_hardness', 0)
    passed = hardness >= 5
    return {'validation_passed': passed, 'log': [f'Hardness check: {passed}']}

def audit_logistics(state: FlooringState):
    return {'log': state['log'] + ['Logistics verified']}

graph = StateGraph(FlooringState)
graph.add_node('validate', validate_material)
graph.add_node('audit', audit_logistics)
graph.set_entry_point('validate')
graph.add_edge('validate', 'audit')
graph.add_edge('audit', END)
graph = graph.compile()