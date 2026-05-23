from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ActuatorState(TypedDict):
    spec: dict
    validation_results: List[str]
    is_compliant: bool

def validate_pneumatic_spec(state: ActuatorState):
    errors = []
    if state['spec'].get('operating_pressure_range_mpa', 0) > 1.0:
        errors.append('Pressure exceeds industrial safety threshold')
    return {'validation_results': errors, 'is_compliant': len(errors) == 0}

def prepare_assembly_workflow(state: ActuatorState):
    return {'validation_results': state['validation_results'] + ['Workflow configured for assembly integration']}

graph = StateGraph(ActuatorState)
graph.add_node('validate', validate_pneumatic_spec)
graph.add_node('workflow', prepare_assembly_workflow)
graph.add_edge('validate', 'workflow')
graph.add_edge('workflow', END)
graph.set_entry_point('validate')
graph = graph.compile()
