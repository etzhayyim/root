from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MailSealState(TypedDict):
    spec_requirements: dict
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_adhesion(state: MailSealState):
    log = ['Adhesion strength check passed'] if state['spec_requirements'].get('strength') else ['Adhesion strength missing']
    return {'validation_log': log}

def finalize_check(state: MailSealState):
    approved = all('passed' in log for log in state['validation_log'])
    return {'is_approved': approved}

graph = StateGraph(MailSealState)
graph.add_node('validate', validate_adhesion)
graph.add_node('finalizer', finalize_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalizer')
graph.add_edge('finalizer', END)
graph = graph.compile()