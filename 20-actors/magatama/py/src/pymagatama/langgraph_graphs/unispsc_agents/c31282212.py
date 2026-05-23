from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AlloyProcurementState(TypedDict):
    part_specs: dict
    validation_results: List[str]
    approved: bool

def validate_alloy_specs(state: AlloyProcurementState):
    specs = state['part_specs']
    results = []
    if 'material_certification' not in specs:
        results.append('Missing MTC')
    return {'validation_results': results, 'approved': len(results) == 0}

graph = StateGraph(AlloyProcurementState)
graph.add_node('validate', validate_alloy_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
