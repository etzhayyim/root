from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class LanguageResourceState(TypedDict):
    content_type: str
    language_scope: List[str]
    validation_status: str

def validate_resource(state: LanguageResourceState):
    if state['content_type'] == 'digital':
        return {'validation_status': 'CHECKING_LICENSE'}
    return {'validation_status': 'APPROVED'}

def compile_graph():
    workflow = StateGraph(LanguageResourceState)
    workflow.add_node('validator', validate_resource)
    workflow.set_entry_point('validator')
    workflow.add_edge('validator', END)
    return workflow.compile()

graph = compile_graph()