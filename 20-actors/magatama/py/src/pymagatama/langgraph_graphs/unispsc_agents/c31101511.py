from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class BerylliumState(TypedDict):
    part_specs: dict
    validation_passed: bool
    compliance_risk: str

def validate_materials(state: BerylliumState):
    print('Validating beryllium composition and weight...')
    state['validation_passed'] = True
    return 'safety_protocol'

def run_safety_protocol(state: BerylliumState):
    print('Initiating hazardous material containment check...')
    state['compliance_risk'] = 'Critical'
    return 'export_review'

def export_review(state: BerylliumState):
    print('Checking dual-use export regulations...')
    return END

graph = StateGraph(BerylliumState)
graph.add_node('validation', validate_materials)
graph.add_node('safety_protocol', run_safety_protocol)
graph.add_node('export_review', export_review)
graph.set_entry_point('validation')
graph.add_edge('validation', 'safety_protocol')
graph.add_edge('safety_protocol', 'export_review')
graph.add_edge('export_review', END)
graph = graph.compile()