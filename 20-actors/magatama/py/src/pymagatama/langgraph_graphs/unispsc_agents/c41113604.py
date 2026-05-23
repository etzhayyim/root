from typing import TypedDict
from langgraph.graph import StateGraph, END

class CapacitanceGraphState(TypedDict):
    model_number: str
    calibration_status: bool
    accuracy_check: bool

def validate_specs(state: CapacitanceGraphState):
    state['accuracy_check'] = True if state.get('model_number') else False
    return 'validated' if state['accuracy_check'] else 'failed'

graph = StateGraph(CapacitanceGraphState)
graph.add_node('validate', validate_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
