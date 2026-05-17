from langgraph.graph import StateGraph, END
from typing import TypedDict
class MeterState(TypedDict):
    spec_data: dict
    validated: bool
    error: str
def validate_specs(state: MeterState):
    required = ['Accuracy class', 'Measurement range']
    all_present = all(k in state['spec_data'] for k in required)
    return {'validated': all_present, 'error': '' if all_present else 'Missing key data'}
def calibrate_workflow(state: MeterState):
    print('Initiating calibration protocol verification.')
    return {'validated': True}
graph = StateGraph(MeterState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', calibrate_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph = graph.compile()