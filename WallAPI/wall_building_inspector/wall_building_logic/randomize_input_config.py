import os
import random

current_path = os.path.dirname(__file__)
input_config_file_path = os.path.join(current_path, "input_config")
with open(input_config_file_path, "w") as fp:
    for profile in range(random.randint(3, 10)):
        sections_number = random.randint(1, 3000)
        fp.write(" ".join([str(random.randint(0, 30)) for section in range(sections_number)]) + "\n")
