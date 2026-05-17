from typing import TypedDict
from langgraph.graph import StateGraph, END

class TrainingMaterialState(TypedDict):
    material_id: str
    content_type: str
    review_status: str

def validate_content(state: TrainingMaterialState):
    # Simulate validation logic for infant care training materials
    print(f'Validating compliance for: {state.material_id}')
    return { 'review_status': 'COMPLIANT' }

def approve_resource(state: TrainingMaterialState):
    return { 'review_status': 'APPROVED' }

graph = StateGraph(TrainingMaterialState)
graph.add_node('validate', validate_content)
graph.add_node('approve', approve_resource)
graph.set_entry_point('validate')
graph.add_edge('validate', 'approve')
graph.add_edge('approve', END)

compiled_graph = graph.compile()