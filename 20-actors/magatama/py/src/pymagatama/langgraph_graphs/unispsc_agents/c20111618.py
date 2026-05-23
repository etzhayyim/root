from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class HydraulicValveState(TypedDict):
    part_number: str
    specifications: dict
    validation_passed: bool
    log: List[str]

def validate_valve_specs(state: HydraulicValveState) -> HydraulicValveState:
    specs = state.get('specifications', {})
    required = ['max_pressure_rating', 'flow_rate_lpm']
    passed = all(k in specs for k in required)
    state['validation_passed'] = passed
    state['log'].append(f'Validation: {passed}')
    return state

def check_dual_use(state: HydraulicValveState) -> HydraulicValveState:
    state['log'].append('Checking export control compliance for high-pressure components')
    return state

graph = StateGraph(HydraulicValveState)
graph.add_node('validate', validate_valve_specs)
graph.add_node('compliance', check_dual_use)
graph.set_entry_point('validate')
graph.add_edge('validate', 'compliance')
graph.add_edge('compliance', END)
graph = graph.compile()
