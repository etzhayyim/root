from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class PaperState(TypedDict):
    paper_specs: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_paper_quality(state: PaperState):
    specs = state['paper_specs']
    logs = []
    compliant = True
    if specs.get('brightness', 0) < 80:
        logs.append('Brightness below threshold')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def check_sustainability(state: PaperState):
    specs = state['paper_specs']
    if not specs.get('fsc_certified', False):
        return {'validation_logs': ['Missing FSC certification'], 'is_compliant': False}
    return {'is_compliant': state['is_compliant']}

graph = StateGraph(PaperState)
graph.add_node('validate', validate_paper_quality)
graph.add_node('sustainability', check_sustainability)
graph.set_entry_point('validate')
graph.add_edge('validate', 'sustainability')
graph.add_edge('sustainability', END)
graph = graph.compile()
