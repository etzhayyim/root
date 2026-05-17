from langgraph.graph import StateGraph, END
from typing import TypedDict
class LabBuildState(TypedDict):
    spec_data: dict
    validation_results: dict
def validate_safety_specs(state: LabBuildState):
    specs = state['spec_data']
    results = {k: 'pass' if v is not None else 'fail' for k, v in specs.items()}
    return {'validation_results': results}
def finalize_procurement(state: LabBuildState):
    return {'validation_results': 'Procurement Ready'}
graph = StateGraph(LabBuildState)
graph.add_node('safety_check', validate_safety_specs)
graph.add_node('finalizer', finalize_procurement)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'finalizer')
graph.add_edge('finalizer', END)
graph = graph.compile()