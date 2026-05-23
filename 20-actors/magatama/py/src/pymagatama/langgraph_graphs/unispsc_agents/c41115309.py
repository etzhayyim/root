from typing import TypedDict
from langgraph.graph import StateGraph, END

class LuxmeterState(TypedDict):
    model_number: str
    calibration_date: str
    is_compliant: bool

def validate_certification(state: LuxmeterState):
    # Business logic for spec validation
    state['is_compliant'] = bool(state['calibration_date'])
    print('Validating calibration status...')
    return state

graph_builder = StateGraph(LuxmeterState)
graph_builder.add_node('validate', validate_certification)
graph_builder.set_entry_point('validate')
graph_builder.add_edge('validate', END)
graph = graph_builder.compile()
