from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class LivestockState(TypedDict):
    livestock_ids: List[str]
    health_status: List[str]
    validation_results: Annotated[List[str], operator.add]

def validate_health(state: LivestockState):
    results = [f'Validated {id}' for id in state['livestock_ids']]
    return {'validation_results': results}

def check_quarantine(state: LivestockState):
    return {'validation_results': ['Quarantine clearance successful']}

graph = StateGraph(LivestockState)
graph.add_node('health_check', validate_health)
graph.add_node('quarantine_check', check_quarantine)
graph.set_entry_point('health_check')
graph.add_edge('health_check', 'quarantine_check')
graph.add_edge('quarantine_check', END)
compiled_graph = graph.compile()