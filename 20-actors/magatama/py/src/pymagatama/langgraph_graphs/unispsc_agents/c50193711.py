from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class TangeloState(TypedDict):
    origin: str
    quality_docs: List[str]
    is_compliant: bool

def validate_food_standards(state: TangeloState):
    state['is_compliant'] = 'ISO22000' in state['quality_docs']
    return {'is_compliant': state['is_compliant']}

workflow = StateGraph(TangeloState)
workflow.add_node('validate', validate_food_standards)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
