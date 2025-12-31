import subprocess

def run_coq(file):
    result = subprocess.run(
        ["coqc", file],
        capture_output=True,
        text=True
    )

    output = result.stdout + result.stderr

    if result.returncode != 0 or "Error:" in output:
        return {
            "status": "FAIL",
            "output": output
        }

    return {
        "status": "PASS",
        "output": output
    }

res = run_coq("ComplianceProof_Example.v")

print(res["status"])

