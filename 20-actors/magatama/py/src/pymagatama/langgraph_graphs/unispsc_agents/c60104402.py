from typing import TypedDict
from langgraph.graph import StateGraph, END

class SpecimenState(TypedDict):
    sample_id: str
    geological_data: dict
    validation_status: bool

def validate_sample(state: SpecimenState):
    # Business logic for geotechnical data validation
    state['validation_status'] = 'composition' in state['geological_data']
    return state

def generate_report(state: SpecimenState):
    print(f'Processing sample {state.get("sample_id")}...')
    return state

graph = StateGraph(SpecimenState)
graph.add_node('validate', validate_sample)
graph.add_node('report', generate_report)
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph.set_entry_point('validate')
graph = graph.compile()