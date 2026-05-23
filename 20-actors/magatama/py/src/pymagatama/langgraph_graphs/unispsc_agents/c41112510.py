from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class FlowIndicatorState(TypedDict):
    specifications: dict
    validation_passed: bool
    inspection_report: str

def validate_specs(state: FlowIndicatorState):
    pressure = state['specifications'].get('pressure_rating', 0)
    state['validation_passed'] = pressure > 0
    return state

def generate_report(state: FlowIndicatorState):
    state['inspection_report'] = 'Validation complete.' if state['validation_passed'] else 'Specs incomplete.'
    return state

graph = StateGraph(FlowIndicatorState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
