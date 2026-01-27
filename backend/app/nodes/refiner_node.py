from ..core.logging import logger
from ..models.state.state import AgentState
from ..agents.refiner import RefinerAgent
from ..agents.judge import JudgeAgent

def refiner_node(state: AgentState):
    logger.info("--- NODE: REFINEMENT ---")
    agent = RefinerAgent()
    refined_request = agent.run(state["extraction"], state["user_request"])
    
    # LLM Judge evaluation for refinement
    judge = JudgeAgent()
    evaluation = judge.evaluate('refinement', str(state["extraction"]) + " | " + state["user_request"], refined_request)
    
    # Add evaluation to list
    evaluations = state.get("evaluations", [])
    evaluations.append(evaluation)
    
    return {"user_request": refined_request, "evaluations": evaluations}