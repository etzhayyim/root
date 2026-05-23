from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END

class MineralState(TypedDict):
    raw_data: dict
    validation_logs: Annotated[Sequence[str], operator.add]
    is_compliant: bool

def validate_purity(state: MineralState) -> dict:
    purity = state['raw_data'].get('purity_percentage', 0)
    if purity >= 95.0:
        return {'validation_logs': ['Purity check passed'], 'is_compliant': True}
    return {'validation_logs': ['Purity check failed'], 'is_compliant': False}

def process_origin(state: MineralState) -> dict:
    return {'validation_logs': ['Origin verification completed']}

workflow = StateGraph(MineralState)
workflow.add_node('validate', validate_purity)
workflow.add_node('verify_origin', process_origin)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'verify_origin')
workflow.add_edge('verify_origin', END)

graph = workflow.compile()
