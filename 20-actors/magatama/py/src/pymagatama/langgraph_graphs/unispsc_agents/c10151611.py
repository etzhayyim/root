from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CompostProcessingState(TypedDict):
    commodity_code: str
    material_type: str
    quality_metrics: dict
    validation_log: List[str]
    is_approved: bool

def validate_material_safety(state: CompostProcessingState) -> CompostProcessingState:
    metrics = state.get('quality_metrics', {})
    heavy_metals = metrics.get('heavy_metals', 0)
    state['is_approved'] = heavy_metals < 50
    state['validation_log'].append(f'Safety check passed: {state['is_approved']}')
    return state

def process_procurement(state: CompostProcessingState) -> CompostProcessingState:
    state['validation_log'].append('Procurement processed for compost distribution')
    return state

def create_compost_graph():
    workflow = StateGraph(CompostProcessingState)
    workflow.add_node('safety_check', validate_material_safety)
    workflow.add_node('process', process_procurement)
    workflow.set_entry_point('safety_check')
    workflow.add_edge('safety_check', 'process')
    workflow.add_edge('process', END)
    return workflow.compile()

graph = create_compost_graph()