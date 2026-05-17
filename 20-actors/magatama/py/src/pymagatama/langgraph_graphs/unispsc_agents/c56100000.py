from typing import TypedDict
from langgraph.graph import StateGraph, END

class FurnitureState(TypedDict):
    spec_data: dict
    validation_result: bool
    compliance_report: str

def validate_furniture_specs(state: FurnitureState):
    required = ['fire_rating', 'material_type', 'load_capacity']
    passed = all(k in state['spec_data'] for k in required)
    return {'validation_result': passed, 'compliance_report': 'Passed' if passed else 'Failed'}

def finalize_order(state: FurnitureState):
    return {'compliance_report': f'Order processed with status: {state['validation_result']}'}

graph = StateGraph(FurnitureState)
graph.add_node('validate', validate_furniture_specs)
graph.add_node('finalize', finalize_order)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()