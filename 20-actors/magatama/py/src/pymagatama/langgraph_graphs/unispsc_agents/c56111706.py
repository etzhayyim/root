from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class FurnitureState(TypedDict):
    part_type: str
    spec_docs: List[str]
    validation_score: float

def validate_part_specs(state: FurnitureState):
    # Simulate CAD/Spec validation for furniture parts
    state['validation_score'] = 0.95 if 'Material' in state['spec_docs'] else 0.0
    return state

def approve_parts(state: FurnitureState):
    print(f'Parts approved with score: {state["validation_score"]}')
    return {'validation_score': 1.0}

graph = StateGraph(FurnitureState)
graph.add_node('validate', validate_part_specs)
graph.add_node('approve', approve_parts)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)
graph = graph.compile()