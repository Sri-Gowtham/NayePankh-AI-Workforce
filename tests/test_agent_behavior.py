import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from agents.supervisor import SupervisorAgent
from tools.db_tools import create_session

def run_test(prompt):
    print(f"\n--- TEST: {prompt} ---")
    sess_res = create_session("default", "supervisor")
    session_id = sess_res["data"]["session_id"]
    supervisor = SupervisorAgent()
    response = supervisor.run(prompt, session_id=session_id)
    print("Response:", response)
    return response

if __name__ == "__main__":
    run_test("Write an Instagram post celebrating our 100th volunteer milestone")
    run_test("How to expand fund")
    run_test("Create a volunteer named Priya")
    run_test("Add intern Ram")
