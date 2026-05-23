from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class StomacherState(TypedDict):
    sample_id: str
    volume_ml: int
    speed_rpm: int
    validation_passed: bool

def validate_specs(state: StomacherState):
    state['validation_passed'] = 100 <= state['volume_ml'] <= 400
    return {'validation_passed': state['validation_passed']}

def process_run(state: StomacherState):
    return {'validation_passed': True}

graph = StateGraph(StomacherState)
graph.add_node('validate', validate_specs)
graph.add_node('operate', process_run)
graph.add_edge('validate', 'operate')
graph.add_edge('operate', END)
graph.set_entry_point('validate')
graph.compile()
