from typing import TypedDict
from langgraph.graph import StateGraph, END
class BatteryState(TypedDict):
    voltage: float
    capacity: float
    status: str
def validate_battery_specs(state: BatteryState):
    if state['voltage'] < 1.4:
        return {'status': 'rejected_low_voltage'}
    return {'status': 'approved'}
graph = StateGraph(BatteryState)
graph.add_node('validate', validate_battery_specs)
graph.set_entry_point('validate')
graph.add_edge('validate', END)
graph = graph.compile()
