from typing import TypedDict
from langgraph.graph import StateGraph, END

class AnalyzerState(TypedDict):
    device_id: str
    calibration_status: bool
    reagent_batch: str
    validation_score: float

def validate_chemistry_analyzer(state: AnalyzerState):
    print(f'Validating analyzer {state["device_id"]}')
    return {'validation_score': 0.95 if state['calibration_status'] else 0.0}

def process_reagents(state: AnalyzerState):
    print(f'Checking reagent batch: {state["reagent_batch"]}')
    return state

graph = StateGraph(AnalyzerState)
graph.add_node("validate", validate_chemistry_analyzer)
graph.add_node("process", process_reagents)
graph.set_entry_point("validate")
graph.add_edge("validate", "process")
graph.add_edge("process", END)
graph = graph.compile()