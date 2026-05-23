from typing import TypedDict
from langgraph.graph import StateGraph, END

class VaccineState(TypedDict):
    batch_id: str
    temperature_logs: list
    validation_status: bool

def validate_cold_chain(state: VaccineState):
    state['validation_status'] = all(temp < 8.0 for temp in state['temperature_logs'])
    return state

def approve_shipment(state: VaccineState):
    return {'validation_status': True} if state['validation_status'] else {'validation_status': False}

graph = StateGraph(VaccineState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('approval', approve_shipment)
graph.add_edge('validate', 'approval')
graph.add_edge('approval', END)
graph.set_entry_point('validate')
graph = graph.compile()
