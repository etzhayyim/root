from typing import TypedDict
from langgraph.graph import StateGraph, END

class FrozenFruitState(TypedDict):
    temp_log: str
    quality_check: bool
    approved: bool

def validate_cold_chain(state: FrozenFruitState):
    # Simulate cold chain validation logic
    temp = float(state.temp_log.replace('C', ''))
    return {'quality_check': temp <= -18.0}

def final_evaluation(state: FrozenFruitState):
    return {'approved': state['quality_check']}

graph = StateGraph(FrozenFruitState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('evaluate', final_evaluation)
graph.add_edge('validate', 'evaluate')
graph.add_edge('evaluate', END)
graph.set_entry_point('validate')
graph = graph.compile()
