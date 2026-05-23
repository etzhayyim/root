from typing import TypedDict, Annotated
from langgraph.graph import StateGraph, END
import operator

class PaperState(TypedDict):
    spec: dict
    validation_results: Annotated[list[str], operator.add]
    is_compliant: bool

def validate_paper_spec(state: PaperState):
    errors = []
    if state['spec'].get('gsm_weight', 0) < 60:
        errors.append('Weight too low for standard printer usage')
    if not state['spec'].get('chlorine_free_certification'):
        errors.append('Missing ECF/TCF certification')
    return {'validation_results': errors, 'is_compliant': len(errors) == 0}

def decision_node(state: PaperState):
    return 'compliant' if state['is_compliant'] else 'non_compliant'

graph = StateGraph(PaperState)
graph.add_node('validate', validate_paper_spec)
graph.add_edge('validate', END)
graph.set_entry_point('validate')
graph = graph.compile()
