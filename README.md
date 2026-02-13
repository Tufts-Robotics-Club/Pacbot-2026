# Pacbot 2026
This is the Pacbot 2026 code!

This is the code running on the pi I think. We will have separate repo for AI etc.

### To set up and run:
In your terminal:
```bash
python -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

### To run simulator flow:
First, run the simulator in the simulator repo with `python simulator/simulator.py`.

One the simulator is up, in this repo, run `motor_controls/motor_loop.py` and then in another terminal run `test_messaging/fake_ai_module.py`. This will allow you to send WASD commands to the robot and see it move.