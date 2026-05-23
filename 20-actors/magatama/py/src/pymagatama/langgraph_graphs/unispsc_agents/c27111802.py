from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LevelState(TypedDict):
    accuracy: float
    material: str
    needs_calibration: bool
    validation_report: List[str]

def validate_precision(state: LevelState):
    if state['accuracy'] > 1.0:
        state['validation_report'].append('Precision exceeds standard tolerance')
    return state

def check_compliance(state: LevelState):
    if state['needs_calibration']:
        state['validation_report'].append('Calibration certificate required for compliance')
    return state

graph = StateGraph(LevelState)
graph.add_node('validate_precision', validate_precision)
graph.add_node('check_compliance', check_compliance)
graph.add_edge('validate_precision', 'check_compliance')
graph.add_edge('check_compliance', END)
graph.set_entry_point('validate_precision')
graph = graph.compile()
