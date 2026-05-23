from typing import TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    spec_data: dict
    validation_result: bool

def validate_medical_specs(state: State):
    reqs = state['spec_data']
    result = all(k in reqs for k in ['iso_cert', 'calibration_date'])
    return {'validation_result': result}

def process_clinical_review(state: State):
    print('Initiating clinical review for pulmonary stress test hardware...')
    return {'validation_result': True}

graph = StateGraph(State)
graph.add_node('validate', validate_medical_specs)
graph.add_node('review', process_clinical_review)
graph.add_edge('validate', 'review')
graph.add_edge('review', END)
graph.set_entry_point('validate')
graph = graph.compile()
