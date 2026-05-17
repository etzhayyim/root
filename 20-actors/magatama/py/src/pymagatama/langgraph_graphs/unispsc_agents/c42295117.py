from typing import TypedDict
from langgraph.graph import StateGraph, END

class WarmingCabinetState(TypedDict):
    temp_range: str
    safety_certs: list
    calibration_status: bool

def validate_specs(state: WarmingCabinetState):
    print('Validating medical warming cabinet specifications...')
    if 'ISO13485' in state['safety_certs'] and state['calibration_status']:
        return {'status': 'approved'}
    return {'status': 'rejected'}

workflow = StateGraph(WarmingCabinetState)
workflow.add_node('validation', validate_specs)
workflow.set_entry_point('validation')
workflow.add_edge('validation', END)
graph = workflow.compile()