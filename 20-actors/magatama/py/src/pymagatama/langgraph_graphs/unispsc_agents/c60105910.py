from typing import TypedDict
from langgraph.graph import StateGraph, END

class SimulatorState(TypedDict):
    model_id: str
    validation_passed: bool
    maintenance_plan: str

def validate_model(state: SimulatorState):
    state['validation_passed'] = state['model_id'].startswith('INF-')
    return state

def plan_maintenance(state: SimulatorState):
    state['maintenance_plan'] = 'Bi-annual hardware check and firmware update' if state['validation_passed'] else 'Manual review required'
    return state

graph = StateGraph(SimulatorState)
graph.add_node('validate', validate_model)
graph.add_node('plan', plan_maintenance)
graph.set_entry_point('validate')
graph.add_edge('validate', 'plan')
graph.add_edge('plan', END)
graph = graph.compile()
