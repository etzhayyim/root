from typing import TypedDict
from langgraph.graph import StateGraph, END

class PlotterState(TypedDict):
    model_id: str
    resolution_dpi: int
    needs_calibration: bool
    approved: bool

def validate_specs(state: PlotterState):
    state['approved'] = state['resolution_dpi'] >= 1200
    return state

def calibration_workflow(state: PlotterState):
    state['needs_calibration'] = True
    return state

graph = StateGraph(PlotterState)
graph.add_node('validate', validate_specs)
graph.add_node('calibrate', calibration_workflow)
graph.set_entry_point('validate')
graph.add_edge('validate', 'calibrate')
graph.add_edge('calibrate', END)
graph = graph.compile()