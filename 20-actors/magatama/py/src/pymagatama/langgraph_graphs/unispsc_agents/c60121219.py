from typing import TypedDict
from langgraph.graph import StateGraph, END

class PaintProcurementState(TypedDict):
    spec_data: dict
    validation_passed: bool

def validate_temp_specs(state: PaintProcurementState):
    temp = state['spec_data'].get('curing_temp', 0)
    state['validation_passed'] = 100 <= temp <= 800
    return state

def safety_check(state: PaintProcurementState):
    print('Checking chemical compliance...')
    return state

graph = StateGraph(PaintProcurementState)
graph.add_node('validate', validate_temp_specs)
graph.add_node('safety', safety_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'safety')
graph.add_edge('safety', END)
app = graph.compile()
