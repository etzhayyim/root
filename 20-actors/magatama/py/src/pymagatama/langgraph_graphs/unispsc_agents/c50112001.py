from typing import TypedDict
from langgraph.graph import StateGraph, END

class MeatProcurementState(TypedDict):
    temp_log: float
    safety_cert: bool
    approved: bool

def validate_cold_chain(state: MeatProcurementState):
    state['approved'] = state['temp_log'] <= 4.0
    return state

def check_compliance(state: MeatProcurementState):
    if state['approved'] and state['safety_cert']:
        return 'ready'
    return 'flagged'

graph = StateGraph(MeatProcurementState)
graph.add_node('validate', validate_cold_chain)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
