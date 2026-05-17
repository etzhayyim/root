from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class ProcurementState(TypedDict):
    product_specs: dict
    validation_errors: List[str]
    is_compliant: bool

def validate_materials(state: ProcurementState):
    content = state['product_specs'].get('materials', '')
    if 'hypoallergenic' not in content.lower():
        state['validation_errors'].append('Material must be hypoallergenic')
    return {'is_compliant': len(state['validation_errors']) == 0}

graph = StateGraph(ProcurementState)
graph.add_node('validation', validate_materials)
graph.set_entry_point('validation')
graph.add_edge('validation', END)
graph = graph.compile()