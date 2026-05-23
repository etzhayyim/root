from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages

class TankProcurementState(TypedDict):
    tank_id: str
    specs: dict
    validation_logs: List[str]
    approved: bool

def validate_specs(state: TankProcurementState):
    logs = [f'Validating material for tank {state["tank_id"]}']
    if state['specs'].get('pressure_rating', 0) < 100:
        logs.append('Pressure rating below safety threshold.')
        return {'validation_logs': logs, 'approved': False}
    return {'validation_logs': logs, 'approved': True}

def finalize_order(state: TankProcurementState):
    return {'validation_logs': state['validation_logs'] + ['Order finalized']}

graph = StateGraph(TankProcurementState)
graph.add_node('validate', validate_specs)
graph.add_node('finalize', finalize_order)
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph.set_entry_point('validate')
graph = graph.compile()
