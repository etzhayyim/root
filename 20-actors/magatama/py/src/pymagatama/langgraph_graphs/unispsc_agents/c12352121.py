from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PolymerProcessingState(TypedDict):
    polymer_id: str
    purity_level: float
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_purity(state: PolymerProcessingState):
    threshold = 99.5
    if state['purity_level'] >= threshold:
        return {'validation_logs': ['Purity validation passed'], 'is_compliant': True}
    return {'validation_logs': ['Purity below threshold'], 'is_compliant': False}

def chemical_safety_check(state: PolymerProcessingState):
    if state['is_compliant']:
        return {'validation_logs': ['Safety clearance verified']}
    return {'validation_logs': ['Safety clearance rejected']}

graph = StateGraph(PolymerProcessingState)
graph.add_node('validate', validate_purity)
graph.add_node('safety', chemical_safety_check)
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph.set_entry_point('validate')
graph = graph.compile()