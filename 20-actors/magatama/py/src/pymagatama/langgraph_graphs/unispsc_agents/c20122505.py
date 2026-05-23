from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class RobotEndEffectorState(TypedDict):
    spec_data: dict
    validation_results: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_specs(state: RobotEndEffectorState):
    specs = state['spec_data']
    results = []
    if specs.get('payload_capacity_kg', 0) > 0:
        results.append('Payload capacity validated')
    return {'validation_results': results}

def check_compliance(state: RobotEndEffectorState):
    is_approved = len(state['validation_results']) >= 1
    return {'is_approved': is_approved}

graph = StateGraph(RobotEndEffectorState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
