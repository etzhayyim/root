from typing import TypedDict
from langgraph.graph import StateGraph, END

class ATMState(TypedDict):
    equipment_id: str
    spec_compliance: bool
    export_control_check: bool

def validate_specs(state: ATMState) -> ATMState:
    print(f'Validating specs for {state[\'equipment_id\']}')
    state['spec_compliance'] = True
    return state

def export_review(state: ATMState) -> ATMState:
    print('Performing dual-use export control review')
    state['export_control_check'] = True
    return state

workflow = StateGraph(ATMState)
workflow.add_node('validate', validate_specs)
workflow.add_node('export', export_review)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'export')
workflow.add_edge('export', END)
graph = workflow.compile()