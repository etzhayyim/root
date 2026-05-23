from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class MushroomState(TypedDict):
    data: dict
    validation_report: List[str]

def validate_freshness(state: MushroomState) -> MushroomState:
    shelf_life = state['data'].get('shelf_life_days', 0)
    if shelf_life < 3: state['validation_report'].append('Urgent transit required')
    return state

def check_certification(state: MushroomState) -> MushroomState:
    if 'freshess_certification' not in state['data']: state['validation_report'].append('Certification missing')
    return state

graph = StateGraph(MushroomState)
graph.add_node('validate', validate_freshness)
graph.add_node('certify', check_certification)
graph.add_edge('validate', 'certify')
graph.add_edge('certify', END)
graph.set_entry_point('validate')
graph = graph.compile()
