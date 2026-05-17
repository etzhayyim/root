from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProphylaxisTankState(TypedDict):
    tank_pressure: float
    material_compliance: bool
    sterilization_validated: bool

def validate_compliance(state: ProphylaxisTankState):
    if state['material_compliance'] and state['sterilization_validated']:
        return 'approve'
    return 'reject'

def check_pressure(state: ProphylaxisTankState):
    return 'compliant' if state['tank_pressure'] < 5.0 else 'fail'

graph = StateGraph(ProphylaxisTankState)
graph.add_node('validate', validate_compliance)
graph.add_node('pressure_test', check_pressure)
graph.add_edge('pressure_test', 'validate')
graph.set_entry_point('pressure_test')
graph.add_edge('validate', END)
graph = graph.compile()