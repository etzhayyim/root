from typing import TypedDict
from langgraph.graph import StateGraph, END

class BagProcurementState(TypedDict):
    bag_specs: dict
    validation_results: list
    is_approved: bool

def validate_specifications(state: BagProcurementState):
    specs = state['bag_specs']
    results = []
    if specs.get('tensile_strength', 0) < 50:
        results.append('Fail: Insufficient tensile strength')
    return {'validation_results': results, 'is_approved': len(results) == 0}

graph = StateGraph(BagProcurementState)
graph.add_node('validate', validate_specifications)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
