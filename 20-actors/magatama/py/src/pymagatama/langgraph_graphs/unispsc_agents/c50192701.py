from typing import TypedDict
from langgraph.graph import StateGraph, END

class FoodSupplyState(TypedDict):
    temp_log: float
    has_haccp: bool
    is_expired: bool

def validate_temp(state: FoodSupplyState):
    return {'is_expired': state['temp_log'] > 5.0}

def check_compliance(state: FoodSupplyState):
    return 'pass' if state['has_haccp'] and not state['is_expired'] else 'fail'

graph = StateGraph(FoodSupplyState)
graph.add_node('validate', validate_temp)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
