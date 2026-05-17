from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class AnalyzerState(TypedDict):
    device_id: str
    calibration_status: bool
    validation_results: List[float]

def validate_calibration(state: AnalyzerState):
    return {'calibration_status': True}

def process_data(state: AnalyzerState):
    print(f'Processing data for {state['device_id']}')
    return {'validation_results': [0.98, 0.99]}

graph = StateGraph(AnalyzerState)
graph.add_node('validate', validate_calibration)
graph.add_node('process', process_data)
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph.set_entry_point('validate')
graph = graph.compile()