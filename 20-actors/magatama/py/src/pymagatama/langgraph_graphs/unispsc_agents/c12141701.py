from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class ResinState(TypedDict):
    material_id: str
    purity: float
    status: str
    logs: Annotated[list[str], operator.add]

def validate_resin(state: ResinState) -> ResinState:
    if state['purity'] < 0.99:
        return {'status': 'rejected', 'logs': ['Purity requirement not met']}
    return {'status': 'validated', 'logs': ['Purity verified']}

def process_resin(state: ResinState) -> ResinState:
    return {'status': 'ready_for_production', 'logs': ['Process parameters configured']}

graph = StateGraph(ResinState)
graph.add_node('validate', validate_resin)
graph.add_node('process', process_resin)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()