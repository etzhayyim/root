from typing import TypedDict
from langgraph.graph import StateGraph, END

class ProcessingState(TypedDict):
    product_name: str
    quality_passed: bool
    temp_log: float

def validate_quality(state: ProcessingState):
    print('Validating lime puree acidity and microbiology...')
    return {'quality_passed': True}

def check_cold_chain(state: ProcessingState):
    print(f'Checking temperature logs: {state.get('temp_log')} C')
    return {'quality_passed': state.get('temp_log') < 5.0}

graph = StateGraph(ProcessingState)
graph.add_node('qc', validate_quality)
graph.add_node('safety', check_cold_chain)
graph.set_entry_point('qc')
graph.add_edge('qc', 'safety')
graph.add_edge('safety', END)
graph = graph.compile()
