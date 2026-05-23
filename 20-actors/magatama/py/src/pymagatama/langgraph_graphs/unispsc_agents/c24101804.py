from typing import TypedDict
from langgraph.graph import StateGraph, END

class StripDoorState(TypedDict):
    specs: dict
    validation_log: list
    approved: bool

def validate_specs(state: StripDoorState):
    required = ['thickness', 'width', 'fire_rating']
    logs = [key for key in required if key not in state['specs']]
    return {'validation_log': logs, 'approved': len(logs) == 0}

graph = StateGraph(StripDoorState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
