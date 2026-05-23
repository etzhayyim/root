from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class CarbonMaterialState(TypedDict):
    material_id: str
    purity_level: float
    process_steps: List[str]
    validation_status: bool

def validate_purity(state: CarbonMaterialState):
    state['validation_status'] = state['purity_level'] >= 99.99
    return {'validation_status': state['validation_status']}

def route_processing(state: CarbonMaterialState):
    if state['validation_status']:
        return 'execute_deposition'
    return END

def execute_deposition(state: CarbonMaterialState):
    state['process_steps'].append('vacuum_chamber_prep')
    state['process_steps'].append('thermal_deposition')
    return {'process_steps': state['process_steps']}

graph = StateGraph(CarbonMaterialState)
graph.add_node('validate', validate_purity)
graph.add_node('execute_deposition', execute_deposition)
graph.set_entry_point('validate')
graph.add_conditional_edges('validate', route_processing)
graph.add_edge('execute_deposition', END)
app = graph.compile()
