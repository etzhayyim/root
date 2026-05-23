from typing import TypedDict, List
from langgraph.graph import StateGraph, END

class CutleryState(TypedDict):
    material: str
    compliance_docs: List[str]
    is_approved: bool

def validate_safety(state: CutleryState):
    # Verify food safety material compliance
    safety_passed = 'food_grade_cert' in state['compliance_docs']
    return {'is_approved': safety_passed}

def final_check(state: CutleryState):
    print(f'Final safety check status: {state.get("is_approved")}')
    return {'is_approved': state.get('is_approved')}

graph = StateGraph(CutleryState)
graph.add_node('safety_check', validate_safety)
graph.add_node('final_process', final_check)
graph.set_entry_point('safety_check')
graph.add_edge('safety_check', 'final_process')
graph.add_edge('final_process', END)
compile_graph = graph.compile()
