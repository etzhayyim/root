from typing import TypedDict
from langgraph.graph import StateGraph, END

class TentState(TypedDict):
    capacity: int
    climate_zone: str
    is_validated: bool

def validate_specs(state: TentState):
    state['is_validated'] = state['capacity'] > 0 and state['climate_zone'] is not None
    return state

def assembly_plan(state: TentState):
    return {'instruction': 'Follow alpine-standard wind anchoring protocol'}

graph = StateGraph(TentState)
graph.add_node('validate', validate_specs)
graph.add_node('plan', assembly_plan)
graph.add_edge('validate', 'plan')
graph.add_edge('plan', END)
graph.set_entry_point('validate')
graph = graph.compile()
