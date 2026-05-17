from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class EggSubstituteState(TypedDict):
    product_id: str
    quality_docs: List[str]
    is_compliant: bool

def validate_food_safety(state: EggSubstituteState):
    state['is_compliant'] = 'Microbiological test report' in state['quality_docs']
    return state

workflow = StateGraph(EggSubstituteState)
workflow.add_node('safety_check', validate_food_safety)
workflow.set_entry_point('safety_check')
workflow.add_edge('safety_check', END)
graph = workflow.compile()