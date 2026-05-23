from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class RadioConfig(TypedDict):
    frequency: float
    specs: dict
    approved: bool

def validate_specs(state: RadioConfig):
    # Business logic for shortwave radio compliance validation
    if state['specs'].get('OutputPowerWatts', 0) > 1000:
        state['approved'] = False
    else:
        state['approved'] = True
    return state

def export_compliance(state: RadioConfig):
    # Dual-use export control checks
    print('Checking export control database...')
    return state

workflow = StateGraph(RadioConfig)
workflow.add_node('validate', validate_specs)
workflow.add_node('compliance', export_compliance)
workflow.set_entry_point('validate')
workflow.add_edge('validate', 'compliance')
workflow.add_edge('compliance', END)
graph = workflow.compile()
