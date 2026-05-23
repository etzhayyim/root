from typing import TypedDict
from langgraph.graph import StateGraph, END

class DrugState(TypedDict):
    batch_id: str
    temp_log: list
    is_compliant: bool

def validate_temp(state: DrugState):
    state['is_compliant'] = all(t <= 8.0 and t >= 2.0 for t in state['temp_log'])
    print(f'Temperature compliance: {state['is_compliant']}')
    return state

def check_quality(state: DrugState):
    print('Checking CoA and sterility documentation...')
    return state

graph = StateGraph(DrugState)
graph.add_node('temp_check', validate_temp)
graph.add_node('quality_check', check_quality)
graph.set_entry_point('temp_check')
graph.add_edge('temp_check', 'quality_check')
graph.add_edge('quality_check', END)
graph = graph.compile()
