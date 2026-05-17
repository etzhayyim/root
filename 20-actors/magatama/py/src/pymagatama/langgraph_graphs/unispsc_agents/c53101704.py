from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    garment_data: dict
    validation_result: bool

def validate_specs(state: State):
    data = state['garment_data']
    valid = all(k in data for k in ['material', 'size', 'care_label'])
    return {'validation_result': valid}

def final_report(state: State):
    status = 'approved' if state['validation_result'] else 'rejected'
    return {'validation_result': status}

graph = StateGraph(State)
graph.add_node('validate', validate_specs)
graph.add_node('report', final_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph.set_entry_point('validate')
graph.set_entry_point('validate')
graph.set_entry_point('validate')