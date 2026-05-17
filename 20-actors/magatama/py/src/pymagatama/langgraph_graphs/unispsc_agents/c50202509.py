from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class JuiceState(TypedDict):
    batch_id: str
    quality_metrics: dict
    approved: bool
    steps: List[str]

def inspect_quality(state: JuiceState):
    metrics = state.get('quality_metrics', {})
    approved = metrics.get('brix', 0) > 10 and metrics.get('ph', 7) < 4.5
    return {'approved': approved, 'steps': state['steps'] + ['quality_check']}

def process_shipment(state: JuiceState):
    return {'steps': state['steps'] + ['dispatch_log']}

graph = StateGraph(JuiceState)
graph.add_node('inspect', inspect_quality)
graph.add_node('dispatch', process_shipment)
graph.add_edge('inspect', 'dispatch')
graph.add_edge('dispatch', END)
graph.set_entry_point('inspect')
graph = graph.compile()