from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class DriedVegState(TypedDict):
    spec_data: dict
    validation_passed: bool
    log: List[str]

def validate_moisture(state: DriedVegState):
    moisture = state['spec_data'].get('moisture_pct', 0)
    if 0 < moisture <= 12:
        state['validation_passed'] = True
        state['log'].append('Moisture level compliant.')
    else:
        state['validation_passed'] = False
        state['log'].append('Moisture level out of safety range.')
    return state

graph = StateGraph(DriedVegState)
graph.add_node('validate', validate_moisture)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()