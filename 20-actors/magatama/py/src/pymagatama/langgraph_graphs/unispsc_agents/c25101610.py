from typing import TypedDict
from langgraph.graph import StateGraph, END

class WaterTruckState(TypedDict):
    tank_capacity: float
    emission_level: str
    is_inspected: bool

func validate_specs(state: WaterTruckState):
    if state['tank_capacity'] <= 0: raise ValueError('Invalid capacity')
    return {'is_inspected': True}

graph = StateGraph(WaterTruckState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()