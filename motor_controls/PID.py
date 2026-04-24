class PID:
    """Generic PID with integral clamp and derivative-on-measurement."""

    def __init__(self, kp, ki=0.0, kd=0.0, i_clamp=1.0, out_clamp=None):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.i_clamp = i_clamp
        self.out_clamp = out_clamp
        self.reset()

    def reset(self):
        self.integral = 0.0
        self._prev_measurement = None

    def update(self, setpoint, measurement, dt):
        if dt <= 0:
            return 0.0

        error = setpoint - measurement
        self.integral += error * dt
        if self.i_clamp is not None:
            self.integral = max(-self.i_clamp, min(self.i_clamp, self.integral))

        if self._prev_measurement is None:
            deriv = 0.0
        else:
            deriv = -(measurement - self._prev_measurement) / dt
        self._prev_measurement = measurement

        out = self.kp * error + self.ki * self.integral + self.kd * deriv
        if self.out_clamp is not None:
            out = max(-self.out_clamp, min(self.out_clamp, out))
        return out
