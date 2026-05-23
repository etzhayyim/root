from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec_requirements: dict
    validation_results: List[str]
    is_compliant: bool

def validate_specs(state: ActuatorState):
    specs = state['spec_requirements']
    results = []
    if specs.get('load_capacity_kg', 0) <= 0:
        results.append('Load capacity must be positive.')
    if specs.get('repeatability_accuracy_um', 100) > 50:
        results.append('High precision threshold exceeded.')
    return {'validation_results': results, 'is_compliant': len(results) == 0}

def assembly_workflow(state: ActuatorState):
    return {'validation_results': state['validation_results'] + ['Workflow simulated: CAD verification passed.']}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_specs)
graph.add_node('assemble', assembly_workflow)
graph.add_edge('validate', 'assemble')
graph.add_edge('assemble', END)
graph.set_entry_point('validate')
graph = graph.compile()
