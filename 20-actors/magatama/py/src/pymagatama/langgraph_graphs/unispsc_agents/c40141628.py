from typing import TypedDict
from langgraph.graph import StateGraph, END

class ValveState(TypedDict):
    pressure_rating: int
    fluid_type: str
    compliance_check: bool

def validate_pressure(state: ValveState):
    state['compliance_check'] = state['pressure_rating'] > 0
    return state

def check_compatibility(state: ValveState):
    print(f'Checking compatibility for fluid: {state.get("fluid_type")}')
    return state

graph = StateGraph(ValveState)
graph.add_node('validate_pressure', validate_pressure)
graph.add_node('check_compatibility', check_compatibility)
graph.set_entry_point('validate_pressure')
graph.add_edge('validate_pressure', 'check_compatibility')
graph.add_edge('check_compatibility', END)
graph = graph.compile()