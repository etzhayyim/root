from typing import TypedDict
from langgraph.graph import StateGraph, END

class FlocculentState(TypedDict):
    batch_id: str
    safety_check: bool
    quality_report: dict

def validate_safety_data(state: FlocculentState):
    print(f'Validating SDS for batch {state['batch_id']}')
    return {'safety_check': True}

def perform_lab_analysis(state: FlocculentState):
    print('Analyzing chemical composition')
    return {'quality_report': {'status': 'passed'}}

graph = StateGraph(FlocculentState)
graph.add_node('safety', validate_safety_data)
graph.add_node('analysis', perform_lab_analysis)
graph.set_entry_point('safety')
graph.add_edge('safety', 'analysis')
graph.add_edge('analysis', END)
graph = graph.compile()