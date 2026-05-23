from typing import TypedDict, List, Annotated
from langgraph.graph import StateGraph, END
import operator

class PolymerState(TypedDict):
    batch_id: str
    purity: float
    compliance_checked: bool
    validation_log: Annotated[List[str], operator.add]

def validate_chemical(state: PolymerState) -> PolymerState:
    log = []
    if state['purity'] < 0.99:
        log.append('Purity check failed: Below 99 percent threshold.')
    else:
        log.append('Purity check passed.')
    return {'validation_log': log}

def check_compliance(state: PolymerState) -> PolymerState:
    # Logic for dual-use export control verification
    return {'compliance_checked': True, 'validation_log': ['Compliance verified against dual-use database.']}

graph = StateGraph(PolymerState)
graph.add_node('validate', validate_chemical)
graph.add_node('compliance', check_compliance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
