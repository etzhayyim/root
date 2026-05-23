from typing import TypedDict
from langgraph.graph import StateGraph, END

class CameraTableState(TypedDict):
    table_id: str
    load_capacity: float
    status: str

def validate_specs(state: CameraTableState):
    if state['load_capacity'] < 5.0:
        return {'status': 'Low Capacity Warning'}
    return {'status': 'Validated'}

def deploy_item(state: CameraTableState):
    print(f'Deploying camera table {state['table_id']}...')
    return {'status': 'Deployed'}

graph = StateGraph(CameraTableState)
graph.add_node('validate', validate_specs)
graph.add_node('deploy', deploy_item)
graph.set_entry_point('validate')
graph.add_edge('validate', 'deploy')
graph.add_edge('deploy', END)
graph = graph.compile()
