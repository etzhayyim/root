from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class CarbonFiberState(TypedDict):
    batch_id: str
    purity_level: float
    specs: dict
    validation_log: Annotated[Sequence[str], operator.add]

def validate_purity(state: CarbonFiberState) -> dict:
    if state['purity_level'] < 0.99:
        return {'validation_log': ['Purity level below industrial standard requirement.']}
    return {'validation_log': ['Purity validation passed.']}

def structural_integrity_check(state: CarbonFiberState) -> dict:
    if state['specs'].get('tensile_strength_mpa', 0) < 3500:
        return {'validation_log': ['Tensile strength does not meet aerospace grade.']}
    return {'validation_log': ['Structural check passed.']}

def define_graph():
    workflow = StateGraph(CarbonFiberState)
    workflow.add_node('validate_purity', validate_purity)
    workflow.add_node('structural_integrity', structural_integrity_check)
    workflow.set_entry_point('validate_purity')
    workflow.add_edge('validate_purity', 'structural_integrity')
    workflow.add_edge('structural_integrity', END)
    return workflow.compile()

graph = define_graph()