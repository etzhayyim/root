from typing import TypedDict, Annotated, List
from langgraph.graph import StateGraph, END

class ReagentState(TypedDict):
    reagent_id: str
    purity_check: bool
    safety_clearance: bool
    analysis_workflow: List[str]

def validate_purity(state: ReagentState) -> ReagentState:
    # Simulate high-precision purity verification logic
    state['purity_check'] = True
    return state

def run_safety_protocol(state: ReagentState) -> ReagentState:
    # Simulate dangerous goods compliance check
    state['safety_clearance'] = True
    state['analysis_workflow'].append('Safety-Checked')
    return state

def define_analysis(state: ReagentState) -> ReagentState:
    state['analysis_workflow'].append('Composition-Analysis')
    return state

graph = StateGraph(ReagentState)
graph.add_node('verify_purity', validate_purity)
graph.add_node('safety_check', run_safety_protocol)
graph.add_node('analysis', define_analysis)
graph.add_edge('verify_purity', 'safety_check')
graph.add_edge('safety_check', 'analysis')
graph.add_edge('analysis', END)
graph.set_entry_point('verify_purity')
app = graph.compile()
