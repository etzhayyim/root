from typing import TypedDict
from langgraph.graph import StateGraph, END

class SuitProcurementState(TypedDict):
    spec_data: dict
    validation_results: list
    is_approved: bool

def validate_fabrics(state: SuitProcurementState):
    fabrics = state['spec_data'].get('fabric_composition', '')
    return {'validation_results': ['Fabric analysis complete'] if fabrics else ['Fabric missing']}

def check_sizing(state: SuitProcurementState):
    sizes = state['spec_data'].get('size_chart', [])
    is_valid = len(sizes) > 0
    return {'validation_results': state['validation_results'] + ['Sizing compliant' if is_valid else 'Sizing missing'], 'is_approved': is_valid}

graph = StateGraph(SuitProcurementState)
graph.add_node('fabric_check', validate_fabrics)
graph.add_node('sizing_check', check_sizing)
graph.set_entry_point('fabric_check')
graph.add_edge('fabric_check', 'sizing_check')
graph.add_edge('sizing_check', END)
graph = graph.compile()
