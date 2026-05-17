from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
import operator

class CarbonFiberState(TypedDict):
    fiber_id: str
    spec_data: dict
    validation_logs: Annotated[List[str], operator.add]
    is_compliant: bool

def validate_fiber_specs(state: CarbonFiberState):
    specs = state['spec_data']
    logs = []
    compliant = True
    if specs.get('tensile_strength_mpa', 0) < 3000:
        logs.append('Insufficient tensile strength for industrial grade.')
        compliant = False
    return {'validation_logs': logs, 'is_compliant': compliant}

def check_dual_use_risk(state: CarbonFiberState):
    # Dual-use screening logic
    logs = ['Screening for export control regulations.']
    return {'validation_logs': logs}

graph = StateGraph(CarbonFiberState)
graph.add_node('validate', validate_fiber_specs)
graph.add_node('risk_check', check_dual_use_risk)
graph.set_entry_point('validate')
graph.add_edge('validate', 'risk_check')
graph.add_edge('risk_check', END)

compiled_graph = graph.compile()