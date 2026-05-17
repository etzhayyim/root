from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    machine_id: str
    validation_checks: List[str]
    status: str

def validate_mechanical_alignment(state: ProcessingState):
    print(f'Checking alignment for {state[\'machine_id\']}')
    return {'validation_checks': ['Alignment Confirmed']}

def perform_quality_assurance(state: ProcessingState):
    print('Running QA on canceling head...')
    return {'status': 'READY'}

graph = StateGraph(ProcessingState)
graph.add_node('alignment', validate_mechanical_alignment)
graph.add_node('qa', perform_quality_assurance)
graph.add_edge('alignment', 'qa')
graph.add_edge('qa', END)
graph.set_entry_point('alignment')

final_graph = graph.compile()