import os
import subprocess

def run_tests():
    examples_dir = "examples"

    # Get all .pasic files in the directory
    pasic_files = sorted([f for f in os.listdir(examples_dir) if f.endswith(".pasic")])

    # Track test results
    failed_tests = []

    for pasic_file in pasic_files:
        pasic_path = os.path.join(examples_dir, pasic_file)
        ans_file = pasic_file.replace(".pasic", ".ans")
        ans_path = os.path.join(examples_dir, ans_file)

        if not os.path.isfile(ans_path):
            print(f"Answer file missing for '{pasic_file}', skipping test.")
            continue

        try:
            # Run "python pasic.py [filename]"
            compile_process = subprocess.run(
                ["python", "pasic.py", pasic_path],
                capture_output=True,
                text=True
            )

            if compile_process.returncode != 0:
                print(f"Compilation failed for '{pasic_file}':\n\n {compile_process.stderr.strip()}\n")
                failed_tests.append(pasic_file)
                continue

            # Determine the name of the generated executable
            executable = pasic_file.removesuffix(".pasic")
            executable_path = f"./{executable}"

            if not os.path.isfile(executable_path):
                print(f"Executable '{executable}' not found after compilation, skipping test.")
                failed_tests.append(pasic_file)
                continue

            # Run the generated executable and capture its output
            run_process = subprocess.run(
                [executable_path],
                capture_output=True,
                text=True
            )

            if run_process.returncode != 0:
                print(f"Execution failed for '{executable}':\n\n {run_process.stderr.strip()}\n")
                failed_tests.append(pasic_file)
                continue

            # Compare the output with the answer file
            output = run_process.stdout.strip()
            with open(ans_path, "r") as ans_file:
                expected_output = ans_file.read().strip()

            if output != expected_output:
                print(f"Test failed for '{pasic_file}':\n\n Output does not match answer file.\n")
                failed_tests.append(pasic_file)
            else:
                print(f"Test passed for '{pasic_file}'.")

            delete_files = subprocess.run(["rm", f"{executable}", f"{executable}.asm", f"{executable}.o"])
            if delete_files.returncode != 0:
                print(f"Failed to delete output files, but doesn't matter.")
        except Exception as e:
            print(f"An error occurred while testing '{pasic_file}': {e}")
            failed_tests.append(pasic_file)

    # Summary
    if failed_tests:
        print("\nTests completed with failures:")
        for test in failed_tests:
            print(f" - {test}")
    else:
        print("\nAll tests passed successfully.")

if __name__ == "__main__":
    run_tests()
