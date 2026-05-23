from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class PenSpecState(TypedDict):
    spec_data: dict
    validation_results: List[str]

def validate_ink_safety(state: PenSpecState):
    sds = state['spec_data'].get('sds_url')
    res = 'Valid' if sds else 'Missing SDS'
    return {'validation_results': [res]}

def check_durability(state: PenSpecState):
    dry_time = state['spec_data'].get('drying_time_sec')
    res = 'Fail' if dry_time > 30 else 'Pass'
    return {'validation_results': [res]}

graph = StateGraph(PenSpecState)
graph.add_node('safety_check', validate_ink_safety)
graph.add_node('durability_check', check_durability)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'durability_check')
graph.add_edge('durability_check', END)
graph = graph.compile()
