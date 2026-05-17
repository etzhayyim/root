from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END

class DrillingState(TypedDict):
    equipment_id: str
    pressure_val: float
    fluid_viscosity: float
    safety_check: bool

def validate_pressure(state: DrillingState) -> DrillingState:
    if state['pressure_val'] > 5000.0:
        print(f'Critical pressure warning for {state["equipment_id"]}')
    return state

def check_safety_standards(state: DrillingState) -> DrillingState:
    state['safety_check'] = state['fluid_viscosity'] > 1.2
    return state

graph = StateGraph(DrillingState)
graph.add_node('validate', validate_pressure)
graph.add_node('safety', check_safety_standards)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()