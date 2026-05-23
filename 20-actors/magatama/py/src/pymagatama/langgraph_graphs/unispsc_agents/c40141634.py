from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    pressure_rating: float
    material: str
    is_compliant: bool

def validate_valve_specs(state: ValveState):
    if state['pressure_rating'] > 0 and state['material'] != 'unknown':
        return {'is_compliant': True}
    return {'is_compliant': False}

def process_procurement(state: ValveState):
    return {'is_compliant': True}

graph = StateGraph(ValveState)
graph.add_node('validate', validate_valve_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
