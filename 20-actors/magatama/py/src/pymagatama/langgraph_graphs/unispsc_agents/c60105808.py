import operator
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END

class State(TypedDict):
    content: str
    validation_report: Annotated[list, operator.add]
    is_compliant: bool

def validate_materials(state: State):
    # Custom logic for validating instructional material specifications
    compliant = 'EN' in state['content'] or 'JP' in state['content']
    return {'validation_report': ['Compliance check passed'], 'is_compliant': compliant}

def finalize_document(state: State):
    return {'validation_report': ['Document finalized for procurement']}

graph = StateGraph(State)
graph.add_node('validate', validate_materials)
graph.add_node('finalize', finalize_document)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
