from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class TimberState(TypedDict):
    spec_data: dict
    validation_results: List[str]

def validate_timber_spec(state: TimberState):
    spec = state['spec_data']
    results = []
    if 'grade_standard' not in spec:
        results.append('Missing grade standard')
    if 'dimensions_mm' not in spec:
        results.append('Missing dimensions')
    return {'validation_results': results}

def process_procurement(state: TimberState):
    return {'validation_results': ['Procurement processing initialized']}

graph = StateGraph(TimberState)
graph.add_node('validate', validate_timber_spec)
graph.add_node('process', process_procurement)
graph.set_entry_point('validate')
graph.add_edge('validate', 'process')
graph.add_edge('process', END)
graph = graph.compile()
