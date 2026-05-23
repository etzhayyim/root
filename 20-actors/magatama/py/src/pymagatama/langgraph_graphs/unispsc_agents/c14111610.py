from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PaperProcurementState(TypedDict):
    paper_type: str
    gsm: int
    is_fsc_certified: bool
    validation_log: Annotated[Sequence[str], operator.add]
    is_approved: bool

def validate_paper_specs(state: PaperProcurementState):
    log = []
    if state['gsm'] < 60 or state['gsm'] > 120:
        log.append(f'Invalid GSM: {state['gsm']}. Must be 60-120.')
    if not state['is_fsc_certified']:
        log.append('Environmental warning: Paper lacks FSC certification.')
    return {'validation_log': log}

def decision_node(state: PaperProcurementState):
    return {'is_approved': len(state['validation_log']) == 0}

graph = StateGraph(PaperProcurementState)
graph.add_node('validate', validate_paper_specs)
graph.add_node('decision', decision_node)
graph.add_edge('validate', 'decision')
graph.add_edge('decision', END)
graph.set_entry_point('validate')
graph = graph.compile()
