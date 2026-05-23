from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class TitaniumState(TypedDict):
    alloy_grade: str
    tests: List[str]
    approved: bool

def validate_specs(state: TitaniumState) -> TitaniumState:
    required = ['ultrasonic', 'chemical_analysis']
    state['approved'] = all(t in state['tests'] for t in required)
    return state

def compile_graph():
    graph = StateGraph(TitaniumState)
    graph.add_node('validate', validate_specs)
    graph.set_entry_point('validate')
    graph.add_edge('validate', END)
    return graph.compile()

graph = compile_graph()
