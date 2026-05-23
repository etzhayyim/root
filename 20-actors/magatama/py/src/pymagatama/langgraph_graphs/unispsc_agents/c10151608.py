from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class MilkProcurementState(TypedDict):
    batch_id: str
    quality_metrics: dict
    approved: bool
    history: Annotated[List[str], list.append]

def validate_quality(state: MilkProcurementState):
    metrics = state.get('quality_metrics', {})
    is_ok = metrics.get('somatic_cell_count', 0) < 200000
    return {'approved': is_ok, 'history': [f'Quality check approved: {is_ok}']}

def route_by_quality(state: MilkProcurementState):
    return 'process' if state['approved'] else 'reject'

graph = StateGraph(MilkProcurementState)
graph.add_node('validate', validate_quality)
graph.add_node('process', lambda s: s)
graph.add_node('reject', lambda s: s)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_by_quality)
graph.add_edge('process', END)
graph.add_edge('reject', END)
graph = graph.compile()
