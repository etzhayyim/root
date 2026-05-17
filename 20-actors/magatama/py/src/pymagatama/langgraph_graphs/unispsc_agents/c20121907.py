from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class HydraulicState(TypedDict):
    pressure_rating: float
    inspection_passed: bool
    validation_log: List[str]

def validate_pressure(state: HydraulicState) -> HydraulicState:
    if state.get('pressure_rating', 0) > 0:
        state['validation_log'].append('Pressure check validated')
        state['inspection_passed'] = True
    else:
        state['validation_log'].append('Invalid pressure rating')
        state['inspection_passed'] = False
    return state

def compile_procurement_graph():
    workflow = StateGraph(HydraulicState)
    workflow.add_node('validate', validate_pressure)
    workflow.set_entry_point('validate')
    workflow.add_edge('validate', END)
    return workflow.compile()

graph = compile_procurement_graph()