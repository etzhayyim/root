from typing import TypedDict
from langgraph.graph import StateGraph, END

class SurveyState(TypedDict):
    specs: dict
    validation_passed: bool
    export_control_flag: bool

def validate_specs(state: SurveyState) -> SurveyState:
    accuracy = state['specs'].get('accuracy', 0)
    state['validation_passed'] = accuracy > 0
    return state

def check_compliance(state: SurveyState) -> SurveyState:
    state['export_control_flag'] = True
    return state

graph = StateGraph(SurveyState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()