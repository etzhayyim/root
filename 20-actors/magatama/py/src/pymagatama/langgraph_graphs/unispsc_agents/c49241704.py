from typing import TypedDict
from langgraph.graph import StateGraph, END

class WaterTestState(TypedDict):
    test_parameters: dict
    validation_status: str
    compliance_log: list

def validate_reagent_expiry(state: WaterTestState):
    # Simulate logic to check shelf life against current procurement date
    state['validation_status'] = 'VALIDATED' if 'expiry' in state['test_parameters'] else 'EXPIRED'
    return state

def run_compliance_check(state: WaterTestState):
    state['compliance_log'] = ['ISO_9001_Verified', 'MSDS_Included']
    return state

graph = StateGraph(WaterTestState)
graph.add_node('validate', validate_reagent_expiry)
graph.add_node('compliance', run_compliance_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
