from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AutopsyScaleState(TypedDict):
    serial_number: str
    calibration_date: str
    material_spec: str
    is_compliant: bool

def validate_certification(state: AutopsyScaleState) -> AutopsyScaleState:
    state['is_compliant'] = bool(state.get('calibration_date') and 'SUS316' in state.get('material_spec', ''))
    return state

def log_inspection(state: AutopsyScaleState) -> AutopsyScaleState:
    print(f'Inspecting scale: {state["serial_number"]}, Status: {state["is_compliant"]}')
    return state

graph = StateGraph(AutopsyScaleState)
graph.add_node('validate', validate_certification)
graph.add_node('log', log_inspection)
graph.set_entry_point('validate')
graph.add_edge('validate', 'log')
graph.add_edge('log', END)
graph = graph.compile()
