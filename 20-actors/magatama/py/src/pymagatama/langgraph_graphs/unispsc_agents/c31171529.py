from typing import TypedDict
from langgraph.graph import StateGraph, END

class BearingSpecState(TypedDict):
    spec_data: dict
    validation_passed: bool
    error_log: list

def validate_dimension(state: BearingSpecState):
    data = state['spec_data']
    passed = 'tolerance' in data and data['tolerance'] < 0.005
    return {'validation_passed': passed, 'error_log': ['Tolerance too high'] if not passed else []}

def validate_material(state: BearingSpecState):
    data = state['spec_data']
    passed = 'hardness' in data and 58 <= data['hardness'] <= 65
    return {'validation_passed': state['validation_passed'] and passed}

graph = StateGraph(BearingSpecState)
graph.add_node('val_dim', validate_dimension)
graph.add_node('val_mat', validate_material)
graph.set_entry_point('val_dim')
graph.add_edge('val_dim', 'val_mat')
graph.add_edge('val_mat', END)
graph = graph.compile()
