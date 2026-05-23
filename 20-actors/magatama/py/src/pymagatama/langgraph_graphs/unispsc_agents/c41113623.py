from typing import TypedDict
from langgraph.graph import StateGraph, END

class InsulationTesterState(TypedDict):
    device_id: str
    test_voltage: int
    calibration_date: str
    is_compliant: bool

def validate_specs(state: InsulationTesterState):
    # Business logic for insulation resistance meter validation
    if state['test_voltage'] > 0 and state['calibration_date']:
        return {'is_compliant': True}
    return {'is_compliant': False}

graph = StateGraph(InsulationTesterState)
graph.add_node("validate", validate_specs)
graph.set_entry_point("validate")
graph.add_edge("validate", END)
graph = graph.compile()
