from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class InkSpecs(TypedDict):
    pigment_type: str
    safety_check: bool
    drying_time_min: int

class InkState(TypedDict):
    specs: InkSpecs
    validation_log: List[str]

def validate_ink(state: InkState):
    log = []
    if state['specs']['pigment_type'] == 'synthetic':
        log.append('Verified synthetic pigment grade')
    state['validation_log'] = log
    return state

workflow = StateGraph(InkState)
workflow.add_node('validate', validate_ink)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()