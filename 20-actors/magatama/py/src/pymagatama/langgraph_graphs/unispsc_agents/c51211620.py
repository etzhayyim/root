from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class FomepizoleState(TypedDict):
    batch_id: str
    temp_log: List[float]
    compliance_cleared: bool

def validate_cold_chain(state: FomepizoleState):
    # Ensure temp logs stay within 2-8 degrees Celsius
    is_valid = all(2 <= t <= 8 for t in state['temp_log'])
    print(f'Cold chain status: {is_valid}')
    return {'compliance_cleared': is_valid}

def final_check(state: FomepizoleState):
    return {'compliance_cleared': state.get('compliance_cleared', False)}

graph = StateGraph(FomepizoleState)
graph.add_node('validate', validate_cold_chain)
graph.add_node('finalize', final_check)
graph.set_entry_point('validate')
graph.add_edge('validate', 'finalize')
graph.add_edge('finalize', END)
graph = graph.compile()
