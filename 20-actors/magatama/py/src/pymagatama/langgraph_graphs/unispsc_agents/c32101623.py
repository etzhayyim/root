from typing import TypedDict
from langgraph.graph import StateGraph, END

class DRAMState(TypedDict):
    specs: dict
    validated: bool
    error_log: list

def validate_specs(state: DRAMState):
    s = state['specs']
    valid = 'clock_speed_mhz' in s and 'capacity_gb' in s
    return {'validated': valid, 'error_log': [] if valid else ['Missing technical parameters']}

def check_compliance(state: DRAMState):
    return {'validated': state['validated'] and (state['specs'].get('temp_range') == 'industrial')}

graph = StateGraph(DRAMState)
graph.add_node('validate', validate_specs)
graph.add_node('compliance', check_compliance)
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph.set_entry_point('validate')
graph = graph.compile()
