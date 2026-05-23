from langgraph.graph import StateGraph, END
from typing import TypedDict
class ProcurementState(TypedDict): model: str; pressure: float; status: str
def validate_specs(state: ProcurementState):
    if state['pressure'] > 5000: return {'status': 'high_pressure_review'}
    return {'status': 'approved'}
def route_step(state: ProcurementState):
    return state['status']
graph = StateGraph(ProcurementState)
graph.add_node('validate', validate_specs)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
