from typing import TypedDict
from langgraph.graph import StateGraph, END

class PEEPState(TypedDict):
    pressure_calibration: float
    valve_material: str
    is_validated: bool

def validate_specs(state: PEEPState):
    if state['pressure_calibration'] > 0 and state['valve_material']:
        return {'is_validated': True}
    return {'is_validated': False}

def process_procurement(state: PEEPState):
    print(f'Processing PEEP valve with material {state['valve_material']}')
    return state

graph = StateGraph(PEEPState)
graph.add_node('validate', validate_specs)
graph.add_node('process', process_procurement)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()
