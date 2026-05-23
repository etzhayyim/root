from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FireproofingState(TypedDict):
    product_name: str
    spec_data: dict
    validation_passed: bool
    compliance_report: str

def validate_materials(state: FireproofingState):
    specs = state['spec_data']
    passed = 'UL_Certification' in specs and specs['Flame_Spread_Rating'] < 25
    return {'validation_passed': passed, 'compliance_report': 'Passed' if passed else 'Non-compliant'}

def generate_safety_doc(state: FireproofingState):
    return {'compliance_report': f'Safety documentation generated for {state[product_name]}'}

graph = StateGraph(FireproofingState)
graph.add_node('validation', validate_materials)
graph.add_node('documentation', generate_safety_doc)
graph.set_entry_point('validation')
graph.add_edge('validation', 'documentation')
graph.add_edge('documentation', END)
graph = graph.compile()
