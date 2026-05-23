from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RotorState(TypedDict):
    model_code: str
    max_rpm: int
    is_compatible: bool
    validation_log: List[str]

def validate_rotor_specs(state: RotorState):
    if state['max_rpm'] < 5000:
        state['is_compatible'] = False
        state['validation_log'].append('RPM below minimum critical requirement.')
    else:
        state['is_compatible'] = True
        state['validation_log'].append('Specs validated.')
    return state

workflow = StateGraph(RotorState)
workflow.add_node('validate', validate_rotor_specs)
workflow.set_entry_point('validate')
workflow.add_edge('validate', END)
graph = workflow.compile()
