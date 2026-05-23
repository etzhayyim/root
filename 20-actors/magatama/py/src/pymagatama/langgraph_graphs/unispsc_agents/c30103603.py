from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class LumberState(TypedDict):
    dimensions: str
    moisture_content: float
    grade_cert: str
    is_approved: bool

def validate_specs(state: LumberState):
    state['is_approved'] = state['moisture_content'] <= 19.0 and state['grade_cert'] == 'Structural'
    return state

def generate_report(state: LumberState):
    print(f'Lumber approval status: {state.get("is_approved")} for specs {state}')
    return state

graph = StateGraph(LumberState)
graph.add_node('validate', validate_specs)
graph.add_node('report', generate_report)
graph.set_entry_point('validate')
graph.add_edge('validate', 'report')
graph.add_edge('report', END)
graph = graph.compile()
