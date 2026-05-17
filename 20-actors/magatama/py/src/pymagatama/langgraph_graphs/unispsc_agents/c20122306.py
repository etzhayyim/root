from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class BearingState(TypedDict):
    part_number: str
    spec_requirements: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_bearing_specs(state: BearingState) -> dict:
    # Specialized validation logic for bearing load specs
    spec = state['spec_requirements']
    if spec.get('load_rating_dynamic', 0) > 0:
        return {'validation_logs': ['Load specs verified'], 'is_approved': True}
    return {'validation_logs': ['Load specs missing'], 'is_approved': False}

def quality_control_check(state: BearingState) -> dict:
    # Simulated inspection logic for industrial components
    return {'validation_logs': ['ISO tolerance verification complete']}

graph = StateGraph(BearingState)
graph.add_node('validate', validate_bearing_specs)
graph.add_node('qc', quality_control_check)
graph.add_edge('validate', 'qc')
graph.add_edge('qc', END)
graph.set_entry_point('validate')
compiled_graph = graph.compile()