from langgraph.graph import StateGraph, END
from typing import TypedDict
class CuttingSpecState(TypedDict): input_data: dict; validation_passed: bool; report: str
def validate_tech(state: CuttingSpecState):
    tech = state['input_data'].get('cutting_technology')
    state['validation_passed'] = tech in ['Laser', 'Plasma', 'Waterjet']
    return state
def generate_report(state: CuttingSpecState):
    state['report'] = 'Validation Successful' if state['validation_passed'] else 'Invalid Tech'
    return state
graph = StateGraph(CuttingSpecState)
graph.add_node('validate', validate_tech)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
