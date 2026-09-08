# Quantizer-Induced Limit Cycles and Nonlinear Settling Dynamics in Belt-Coupled Serial-Bus Actuators

**Source:** deep-research response from Gemini, 6 September 2026, run against
the prompt in `D48_followup_research_prompt.md` (the second research pass,
following up on `D40_resonance_research_claude.md`/`_gemini.md` now that
Session 25's actual experiments contradicted several of that first pass's
predictions). Kept verbatim as the reasoning is the record — do not edit in
place; correct or supersede in D48's own entry instead. **A parallel answer
from Claude to the same prompt, run in a separate session, is expected next
session — file it alongside this one as `D48_followup_research_claude.md`
when it arrives, do not overwrite this file.**

---

## Theoretical Analysis of the Quantizer-Induced Limit Cycle

The empirical observation of a sustained limit cycle with an oscillation period repeating to four significant figures ($0.2668\,\text{s}$, $0.2670\,\text{s}$, $0.2668\,\text{s}$, corresponding to a frequency $f \approx 3.748\,\text{Hz}$) and an oscillating current amplitude of $0.026\text{--}0.058\,\text{A}$ provides conclusive proof of a deterministic digital non-linearity rather than an unforced mechanical resonance. When an actuator's feedback loop discretizes position into uniform spatial quanta ($\Delta = 0.06^\circ/\text{count}$ via the 12-bit magnetic encoder), the governing differential equations of the closed-loop system collapse into a piecewise-continuous, state-dependent non-linear map.

The classical describing function formulation demonstrates why uniform spatial quantization triggers sustained orbital limit cycles. Assuming a fundamental sinusoidal displacement crossing a quantization threshold, $e(t) = A \sin(\omega t)$, the spatial staircase characteristic is represented in the frequency domain by its real, amplitude-dependent describing function $N(A)$:

$$N(A) = \frac{4 \Delta}{\pi A} \sum_{k=1}^{M} \sqrt{1 - \left(\frac{(2k - 1)\Delta}{2A}\right)^2}$$

For a single-count hunting cycle oscillating across a single discrete boundary with amplitude $A \in [\Delta/2, \Delta]$, the describing function simplifies to:

$$N(A) \approx \frac{4 \Delta}{\pi A} \sqrt{1 - \left(\frac{\Delta}{2A}\right)^2}$$

In the complex plane, the negative inverse describing function locus, $-1/N(A)$, is confined entirely to the negative real axis, extending from $-\infty$ as $A \to \Delta/2$ down to $0^-$ as $A \to \infty$. According to the harmonic balance criterion, a stationary limit cycle exists at any frequency $\omega$ where the open-loop linear transfer function $G(j\omega)$ intersects this locus, satisfying $G(j\omega) = -1/N(A)$. Because any physical electromechanical drive with compliance, inertia, digital sampling zero-order hold (ZOH) delay, and electrical time constants exhibits a phase lag exceeding $-180^\circ$ at intermediate frequencies, the linear Nyquist trajectory $G(j\omega)$ inevitably cuts across the negative real axis.

In digital motion control literature, particularly the foundational framework established by Peterchev and Sanders, two non-negotiable conditions must be met to eliminate quantizer-induced limit cycling in digitally controlled pulse-width-modulated drives:

1. The zero-error bin of the feedback quantizer must map to an allowable, non-oscillating steady-state control effort that matches the static friction and load-holding requirements of the physical plant.
2. The loop gain at the discrete Nyquist folding frequency must remain sufficiently low that high-frequency differentiation noise cannot fold back into self-sustaining sub-harmonic limit cycles.

The empirical sweep across position derivative gain ($K_D$, Register 22) demonstrated an apparent non-monotonic failure distribution: baseline $D32$ failed $7/10$ trials, $D24$ failed $5/10$, $D16$ failed $2/10$, and $D8$ worsened to $9/10$. Subsequent bracketing around $D16$ ($D14=7/8$, $D18=8/8$, $D20=6/8$) established via Fisher's exact test that $D16$ was an isolated statistical artifact ($p = 0.35$ against $D24$; $p = 0.070$ against baseline) rather than a robust physical optimum.

Control theory indicates that derivative gain acting on raw quantized position is fundamentally incapable of resolving a single-count limit cycle. In embedded motion firmware, the derivative term is evaluated numerically using discrete backward differences:

$$u_D[k] = K_D \frac{y_q[k] - y_q[k-1]}{T_s}$$

When the output shaft settles near a boundary line, minute physical vibrations toggle $y_q[k]$ by $\pm 1\,\text{count}$. Over a single sample interval $T_s$, the computed derivative term outputs an instantaneous Dirac-like torque impulse proportional to $\pm K_D \Delta / T_s$. At high derivative settings ($D > 24$), this impulse delivers high instantaneous power to the motor windings. Combined with the unavoidable computational transport delay ($\tau_d \approx T_s/2$) and motor phase lag, this impulse arrives out of phase with true rotor velocity, injecting net energy into the oscillation and driving high-frequency chattering. Conversely, when derivative gain is drastically attenuated ($D < 12$), the control loop lacks electronic damping. When the position proportional term ($K_P$, Register 21) pushes the rotor toward the setpoint, the mechanical plant possesses insufficient viscous damping to dissipate kinetic energy before crossing the target count, overshooting into the opposing count and maintaining the cycle.

The intermediate setting ($D16$) merely achieved a delicate, non-robust neutralization where backward-difference kick happened to offset the proportional step under one specific set of approach initial conditions. Because the describing function gain $N(A)$ approaches infinity as oscillation amplitude approaches the threshold boundary, this balance possesses an infinitesimal basin of attraction. Derivative gain is the wrong parameter axis for mitigating spatial quantization limit cycles; relying on position differentiation amplifies sensor noise without addressing the fundamental phase lag of the drive train.

## Nonlinear Drive Dynamics and Approach Velocity

The experimental outcome wherein every deliberate softening of the final corrective approach leg (reducing velocity to $10^\circ/\text{s}$ or $5^\circ/\text{s}$, lowering acceleration to $10\text{--}20$, or shortening the overshoot from $1.5^\circ$ to $0.5^\circ$) made settling performance strictly worse ($8/8$ and $6/8$ failures, compared to $4/8$ with the default unsoftened move) contradicts linear intuition but aligns directly with nonlinear tribology, cogging detents, and discrete trajectory integration.

The transmission of the STS3215 incorporates an iron-core DC brush motor coupled to a multi-stage metal gearhead with a high overall reduction ratio ($N \approx 345:1$). In such high-ratio transmissions, friction behavior at ultra-low velocities is governed by the classical Stribeck friction model:

$$\tau_f(v) = \left[ \tau_c + (\tau_s - \tau_c) e^{-(v/v_s)^2} \right] \text{sgn}(v) + \sigma_v v$$

where $\tau_s$ is the static breakaway torque, $\tau_c$ is the Coulomb kinetic friction torque ($\tau_s > \tau_c$), $v_s$ is the characteristic Stribeck velocity threshold, and $\sigma_v$ is the viscous damping coefficient.

In the boundary lubrication regime ($0 < |v| < v_s$), the friction characteristic exhibits a negative derivative with respect to velocity:

$$\frac{d\tau_f(v)}{dv} < 0$$

A negative slope in the force-velocity relationship acts as an energy source, introducing negative mechanical damping. When the host controller commands a crawl speed of $5^\circ/\text{s}\text{--}10^\circ/\text{s}$ at the geartrain output, the internal motor armature rotates at only $1725^\circ/\text{s}\text{--}3450^\circ/\text{s}$ ($4.8\text{--}9.6\,\text{rev/s}$). Given the high surface shear across multiple spur gear stages and grease churning resistance, this operating point forces the drive train to spend substantial transit time submerged within the negative-damping Stribeck regime, triggering self-excited friction oscillations before the setpoint is reached.

Furthermore, small iron-core DC motors suffer from magnetic cogging torque, produced by the variable magnetic reluctance between the permanent rotor magnets and the stator armature laminations. To prevent actuator deadband stalling from cogging and gear train friction, the STS3215 firmware includes Register 24 (Minimum Startup Force), configured with a factory default value of $16/1000$ (a permanent minimum baseline PWM command applied whenever position error is non-zero).

During an unsoftened, standard-speed approach, the actuator arrives at the final position with significant rotor kinetic energy, $E_k = \frac{1}{2} J_m \omega_m^2$. As the final encoder count is reached, the control loop drops its drive command, allowing the rotor's momentum to push past tooth cogging detents and seat firmly into the static friction well ($\tau_{applied} < \tau_s$) near the center of the encoder count window.

Conversely, during a softened $5^\circ/\text{s}$ corrective leg, kinetic energy is effectively zero. The internal trajectory planner commands sub-count setpoint increments every control cycle. The motor repeatedly stalls against geartrain stiction and stator cogging. Position error accumulates until the combination of the proportional term and Register 24 exceeds $\tau_s$. Because static friction immediately drops to the lower dynamic friction level ($\tau_s \to \tau_c$), the motor releases with an explosive micro-lurch, jumping across the target count boundary. The error instantly changes sign, commanding reverse torque and repeating the cycle. A softened approach strips the actuator of the kinetic energy necessary to clear the Stribeck barrier cleanly, stranding the rotor on the switching threshold of the position quantizer.

## Drive-Train Compliance and Settling Blind Spots

The finding that a full-travel $150^\circ$ preceding move reliably degraded settling compared to a short $5^\circ$ move—despite the final corrective leg being executed under identical dynamics after the firmware reported motion completion—highlights the fundamental divergence between collocated sensing and non-collocated structural compliance.

The mechanical assembly forms a classical two-mass resonant drive system. The internal motor rotor and high-ratio gearbox constitute the driving inertia ($J_m$), while the external bench rig load represents the driven inertia ($J_L$), coupled via the torsional elasticity of the timing belt ($k_b$):

$$J_m \ddot{\theta}_m + b_m \dot{\theta}_m + \frac{k_b}{N^2}\left(\theta_m - N\theta_L\right) = \tau_m$$
$$J_L \ddot{\theta}_L + b_L \dot{\theta}_L - k_b\left(\frac{\theta_m}{N} - \theta_L\right) = 0$$

In structural dynamics and motion control literature, this phenomenon is formally termed residual vibration, elastodynamic settling lag, or quenched settling error. During a gross motion of $150^\circ$, high acceleration and deceleration torques cause considerable elastic deflection across the timing belt spans, accompanied by structural tooth deflection and carcass hysteresis. When the motor reaches the target region and decelerates, significant elastic potential energy is stored in the compliant belt:

$$U = \frac{1}{2} k_b \Delta\theta_{belt}^2$$

The STS3215 firmware evaluates motion state through Register 66 (moving). The microcontroller asserts or clears this bit based strictly on its collocated magnetic encoder at the output shaft, typically testing whether output shaft displacement remains below a fixed count threshold over a short temporal window:

$$\frac{|\theta_m[k] - \theta_m[k-M]|}{M \cdot T_s} < v_{thresh}$$

Because the internal 12-bit encoder is mounted before the belt drive, it cannot measure the deflection of the belt or the independent ringing of the load inertia $J_L$. When the motor halts and the firmware clears the moving flag, the external load continues to vibrate at its anti-resonant natural frequency:

$$\omega_{ar} = \sqrt{\frac{k_b}{J_L}}$$

This ringing transmits a dynamic reaction torque, $\tau_{reac} = k_b (\theta_L - \theta_m/N)$, across the belt and back into the servo output horn. A $150^\circ$ move excites this compliant mode far more aggressively than a $5^\circ$ move. Consequently, when the host script immediately issues the final corrective command upon reading moving == 0, it dispatches the final leg into an actively vibrating, non-quenched mechanical transmission.

To verify the presence of lingering mechanical vibration, the host should stream Present Current (Register 69) and Present Load (Register 60) at 100 Hz for $1.0\,\text{s}$ after Register 66 transitions to 0. If residual elastodynamic energy is present, the current trace will exhibit an exponentially decaying sinusoid at frequency $\omega_{ar}$, even while the reported position remains locked to a single value.

To eliminate this dynamic interference, a mandatory dwell interval $T_{dwell}$ must be enforced between the clearing of the overshoot moving flag and the initiation of the final approach leg. The minimum dwell time required for the residual elastic vibration to attenuate to an acceptable tolerance band $\epsilon_{tol}$ is defined by the damping ratio $\zeta$ and the natural frequency:

$$T_{dwell} \ge \frac{-\ln(\epsilon_{tol})}{\zeta \omega_{ar}} \approx \frac{3 \text{ to } 4}{\zeta \sqrt{k_b / J_L}}$$

For typical polyurethane timing belts exhibiting modest structural damping ($\zeta \approx 0.03\text{--}0.06$), an enforced dwell time of $200\text{--}350\,\text{ms}$ ensures complete mechanical dissipation of stored belt energy prior to final setpoint capture.

## Physical Mechanisms of Left/Right Directional Asymmetry

Testing demonstrated a pronounced directional asymmetry: the $+60^\circ$ position exhibited partial settling improvements under certain register modifications, whereas the mirror-image $-60^\circ$ setpoint suffered an unbroken $10/10$ failure rate across all tested parameters, move sizes, approach directions, and deadband settings. Because the internal PID control law, velocity profiles, and register values are mathematically direction-symmetric, this divergence must originate in asymmetric physical forces or non-uniform mechanical geometry.

The physical mechanisms underlying this directional behavior are evaluated below, ranked according to their observability via the servo's internal telemetry registers (Register 56: Position, Register 60: Load, Register 62: Voltage, Register 69: Current) versus requiring external bench metrology.

| Rank | Physical Failure Mechanism | Dynamic Interaction | Telemetry Diagnosability | Telemetry Diagnostic Methodology |
|---|---|---|---|---|
| 1 | Gravitational Bias / Static Load Moment | Rig center of mass is offset from the center of rotation. A static gravity torque $T_g(\theta)$ acts on the output shaft. At $+60^\circ$, gravity imposes a unidirectional load that forces gear teeth and belt teeth against a single contact flank, quenching hunting. At $-60^\circ$, gravity acts in opposition or hovers near zero net torque, allowing gear teeth to float within the backlash gap. | Very High | Compare steady-state Present Current (Reg 69) and Present Load (Reg 60) when holding at $+60^\circ$ versus $-60^\circ$. An offset $\Delta I = |I_{+60}| - |I_{-60}| > 30\,\text{mA}$ confirms static gravitational loading. |
| 2 | Asymmetric Belt Span Compliance | Typical single-stage belt rigs feature asymmetric tensioning geometries. Moving toward $+60^\circ$ tensions the short, rigid belt span, whereas moving toward $-60^\circ$ pulls against the longer, compliant span. The lower structural stiffness of the long span drops the local resonant frequency and broadens the limit-cycle basin of attraction. | High | Monitor Present Current (Reg 69) and tracking error during steady-state slewing toward positive versus negative angles. The more compliant direction exhibits higher phase lag and pronounced dynamic current ripple. |
| 3 | Pulley Runout and Pitch Eccentricity | Pulley bore tolerances, set-screw tightening tilt, or pitch circle runout produce radial eccentricity ($e_r$). Belt tension varies sinusoidally as a function of absolute angle: $T(\theta) = T_0 + k_{rad} e_r \sin(\theta + \phi)$. At $-60^\circ$, belt tension reaches a minimum (promoting tooth unseating and backlash chatter) or a maximum (causing bearing binding and elevated breakaway torque $\tau_s$). | Moderate | Execute a slow, continuous $360^\circ$ rotation while logging Present Current (Reg 69). Radial eccentricity reveals a distinct once-per-revolution ($1\times$ rev) fundamental sinusoidal variation in current draw. |
| 4 | Localized Gearbox Backlash / Pinion Tooth Flaws | Multi-stage spur geartrains exhibit rotational pitch errors, localized burrs, or non-uniform casing bore wear. At $-60^\circ$, internal gears engage an imperfect tooth flank that increases mechanical backlash or friction variation. | Low | Requires disabling drive torque (Reg 40 = 0) and manually profiling output backlash with a mechanical dial test indicator across both positions. |

Gravitational torque bias is the most probable physical cause for the total settling failure at $-60^\circ$. If the mechanical rig is uncounterbalanced, the gravitational moment vector either aligns with the final approach leg or cancels baseline friction, placing the gear teeth in a floating state within the deadband. Conversely, a unidirectional holding torque pre-loads gear teeth against one flank, creating a mechanical constraint that suppresses single-count toggling.

## Cascaded Architecture and Velocity-Loop Register Tuning

The Waveshare ST3215 and Feetech STS3215 firmware does not operate as a single-loop PID controller. The control architecture consists of a cascaded topology where the outer position loop feeds setpoints into an inner velocity/current loop. The primary inner-loop parameters are:

- Register 37: Speed closed loop P proportional coefficient (Factory default: 10)
- Register 39: Velocity closed loop I integral coefficient (Factory default: 200)
- Register 41: Goal Acceleration ramp (Factory default: 0 = unprofiled step command; 1–254 = trapezoidal acceleration profiling)

The empirical observation of an oscillation period of precisely $0.2668\,\text{s}$ ($f \approx 3.75\,\text{Hz}$) provides insight into the control dynamics. Pure spatial quantization hunting against linear inertia typically generates limit cycles at high frequencies ($>50\text{--}100\,\text{Hz}$), governed by sample rates and electrical time constants. A period of several hundred milliseconds points directly to velocity integrator windup driven by Register 39 (Velocity I = 200) operating in series with mechanical breakaway friction.

The sequence of this instability follows a distinct progression:

1. When the actuator halts within a single count of the target, the outer position loop generates a small, non-zero target velocity proportional to the remaining error: $v_{target} = K_{P,pos} \cdot e_{pos}$. Because static friction prevents immediate motion, actual velocity remains zero ($v_{meas} = 0$).
2. The resulting velocity error, $e_v = v_{target} - 0$, is integrated over time by Register 39: $u_{pwm}(t) = K_{I,vel} \int_0^t e_v(\tau)\,d\tau$. The internal PWM duty cycle ramps upward until the motor's electromagnetic torque exceeds the static breakaway threshold $\tau_s$.
3. The rotor breaks away, immediately accelerating as friction drops to dynamic levels ($\tau_c$).
4. The rotor crosses the single-count target boundary, inverting the sign of position error $e_{pos}$ and commanding a reverse target velocity.
5. However, the velocity integrator remains saturated at a high positive value. The controller cannot reverse motor current until this accumulated charge is unwound and integrated in the negative direction.

This integration, breakaway, overshoot, desaturation, and reverse breakaway sequence produces a sustained limit cycle whose period matches the observed $0.267\,\text{s}$ waveform.

Simultaneously, Register 37 (Speed P = 10) governs pure velocity feedback damping ($u \propto -K_{P,vel} v_{meas}$). Unlike position derivative gain (Register 22), which differentiates a quantized spatial signal and produces severe torque spikes, the inner velocity loop filters velocity estimates across multi-sample windows or timing interrupts. Increasing Register 37 injects genuine viscous damping into the motor shaft without amplifying single-count position noise.

Register 41 (Goal Acceleration) controls internal setpoint profile generation. When set to 0, incoming position commands are treated as step inputs, commanding infinite acceleration and delivering high jerk that excites the belt's compliant modes. Assigning values between 20 and 100 enforces controlled acceleration ramps ($a \approx \text{Reg} \times 100\,\text{steps/s}^2$), preventing inertial shock loading from disturbing the compliant belt transmission during setpoint capture.

To optimize these parameters, the registers must be tested systematically. Modifying Registers 37 and 39 requires unlocking the EEPROM via Register 55 (Lock = 0).

| Execution Order | Target Register | Default Setting | Sweep Candidates | Primary Control Function & Dynamic Objective |
|---|---|---|---|---|
| Step 1 | Register 39 (Velocity I) | 200 | 0, 10, 25, 50 | **Eliminate Integrator Windup**: Setting Register 39 to 0 completely terminates error integration at standstill, eliminating the $3.75\,\text{Hz}$ limit cycle. Modest non-zero values (10–25) preserve dynamic velocity-tracking stiffness under continuous motion without causing hunting at rest. |
| Step 2 | Register 37 (Velocity P) | 10 | 15, 20, 30, 45 | **Inject Electronic Viscous Damping**: Increasing Register 37 introduces smooth, back-EMF-like software damping directly into the rotor velocity loop, dissipating energy at the target threshold without generating backward-difference noise. |
| Step 3 | Register 41 (Acceleration Ramp) | 0 | 30, 60, 90, 120 | **Attenuate Inertial Jerk**: Enforcing a controlled acceleration ramp softens the deceleration profile of the final approach, preventing the shock loading that excites belt compliance. |

## Non-Uniform and Hysteretic Deadband Architectures

A flat spatial deadband eliminates hunting by zeroing controller output when position error falls within a fixed count window:

$$e_d = \begin{cases} 0, & |e| \le \delta \\ e - \delta \cdot \text{sgn}(e), & |e| > \delta \end{cases}$$

Testing this standard deadband on the STS3215 confirmed its performance limitations. A deadband of 1 count reduced failures to $4/10$ at $+60^\circ$ (with a mean error of $0.042^\circ$), but a deadband of 2 counts degraded positioning accuracy to a maximum error of $0.190^\circ$. At the worse-performing $-60^\circ$ angle, both settings failed $10/10$, with 2 counts of deadband allowing position errors up to $1.480^\circ$ as the load slipped within the unpowered threshold.

Precision servomechanisms resolve this trade-off using hysteretic (dual-threshold) or stateful deadbands:

- **Tracking State**: During active trajectory motion, the deadband is set to zero ($\delta = 0$). The position loop maintains full proportional gain to minimize following error.
- **Settling State**: When the shaft enters the target window ($|e| \le \delta_1 = 1\,\text{count}$) and velocity drops below a threshold for $N$ consecutive sample periods, the system transitions to a settled state. The deadband boundary dynamically expands to an outer threshold $\delta_2$ (e.g., $2\text{--}3\,\text{counts}$).
- **Disturbance Re-engagement**: Small disturbances within $\delta_2$ produce zero corrective torque, leaving the rotor locked by static friction and eliminating hunting. Only if an external load forces the error beyond $\delta_2$ does the controller re-engage full restorative gain.

By separating the entry threshold ($\delta_1$) from the exit threshold ($\delta_2$), the controller creates a finite hysteresis band that prevents single-count toggling while preserving high steady-state accuracy.

However, the memory architecture of the Feetech STS3215 presents significant barriers to running this strategy natively:

- The servo exposes two deadband registers: Register 26 (CW Dead Zone) and Register 27 (CCW Dead Zone), both defaulted to 1 count.
- Registers 26 and 27 are stored in non-volatile EEPROM (addresses $0\text{--}39$). Modifying them requires unlocking the memory (Register 55 = 0), issuing write commands, and re-locking (Register 55 = 1).
- EEPROM write cycles introduce bus communication latencies of several milliseconds and suffer from physical flash endurance limits (typically 10,000 to 100,000 write cycles). Continuously toggling Registers 26 and 27 on every positioning move will permanently destroy the microcontroller's flash memory sectors within tens of operational hours.
- Because the vendored SDK (`libraries/SCServo/`) provides access only to exposed serial register packets and contains no hooks into the internal 1-kHz control interrupt, true hysteretic deadband processing cannot be executed directly on the servo's internal MCU.

Nevertheless, equivalent hysteretic behavior can be achieved from the host controller by operating exclusively on volatile RAM registers (addresses $40\text{--}49$), which permit unlimited high-speed writes without memory degradation:

- **Host-Side Supervisory Torque Clamping**: The host issues the position command with nominal torque (Register 48: Torque Limit = 1000). The host polls Present Position (Register 56) over the 1-Mbps serial bus. Once the feedback satisfies $|e| \le 1\,\text{count}$ for 5 consecutive polling frames ($50\,\text{ms}$ at 100 Hz), the host writes Register 48 (Torque Limit) = 0 or a relaxed holding value (e.g., $80/1000$). The motor enters a relaxed holding state where mechanical stiction locks the rotor in place, immediately extinguishing the limit cycle. If an external disturbance subsequently pulls the shaft beyond $\pm 3\,\text{counts}$, the host restores Register 48 to $1000$.
- **Dynamic Goal Snapping**: When the host detects that the motor has reached the target zone and is oscillating between two adjacent counts ($k$ and $k+1$), it reads the current instantaneous position from Register 56 and immediately writes that exact integer into Goal Position (Register 42). This zeros the error term, terminating proportional drive and halting the limit cycle without inducing mechanical displacement.

## Sequenced Remediation Roadmap and Actionable Protocol

To systematically resolve the settling jitter and eliminate limit cycling across all test angles, the remediation protocol should proceed through the following experimental phases:

### Phase 1: Inner Velocity-Loop Reconfiguration (Registers 37 & 39)

The primary intervention is terminating the internal velocity integrator windup that produces the $0.267\,\text{s}$ limit cycle.

1. Unlock the EEPROM by sending a write command to Register 55 (Lock = 0).
2. Suppress the velocity loop integrator: Write Register 39 (Velocity I) = 0.
3. Increase velocity proportional damping: Write Register 37 (Velocity P) = 25 (test bracket: $15, 20, 25, 35$; default is 10).
4. Re-lock the EEPROM by writing Register 55 (Lock = 1).
5. Re-run the high-speed 100-Hz position and current telemetry trace at $+60^\circ$ and $-60^\circ$.

**Success Criterion**: The $0.2668\,\text{s}$ reversal cycle must be completely absent. If the shaft remains stable within a single count without toggling, the limit cycle is resolved.

### Phase 2: Trajectory Ramp and Approach Velocity Optimization (Registers 41 & 46)

Address inertial shock loading while avoiding the negative-damping Stribeck friction regime.

1. Restore the final anti-backlash corrective approach leg to standard travel speed ($60\text{--}100^\circ/\text{s}$), abandoning the softened $5\text{--}10^\circ/\text{s}$ crawling velocities to ensure the rotor does not stall in the Stribeck region.
2. Enable internal acceleration profiling: Write RAM Register 41 (Goal Acceleration) = 60 (test bracket: $30, 60, 90$; default is 0).

**Success Criterion**: Smooth deceleration trajectories without current spikes during final setpoint interception.

### Phase 3: Transmission Compliance and Settle-Time Dwell Enforcement

Decouple the non-collocated belt and load oscillations from the final corrective leg.

1. In the host-side control script, insert a mandatory settle dwell time: Set $T_{dwell} = 250\,\text{ms}$ immediately following the transition of Register 66 (moving) to 0 on the overshoot leg, before issuing the final position command.
2. Verify via streaming of Present Current (Register 69) that residual belt oscillations have completely damped out prior to launching the final approach move.

### Phase 4: Diagnostic Isolation of Directional Asymmetry

Resolve the performance disparity between the $+60^\circ$ and $-60^\circ$ positions.

1. Command the servo to hold at $+60^\circ$ and log Present Current (Register 69) and Present Load (Register 60) over a 2-second stationary interval; repeat the measurement at $-60^\circ$.
2. If static holding currents diverge significantly ($|I_{+60}| - |I_{-60}| > 30\,\text{mA}$), a gravitational moment is acting on the rig. Install mechanical counterweights or balance springs to equalize static holding torque across the operating range.
3. If holding currents are identical, inspect the mechanical drive:
   - Measure belt pretension across both spans to confirm balanced compliance.
   - Mount a dial indicator on the drive pulley to measure radial runout ($e_r$).
   - Inspect the output shaft for angular play with torque disabled (Register 40 = 0) to check for localized geartrain wear.

### Phase 5: Host-Supervised RAM Deadband Clamping

If the servo continues to exhibit single-count boundary dithering when the physical rotor happens to land precisely on an encoder transition threshold:

1. Maintain default EEPROM deadbands (Registers 26 and 27 = 1) to protect flash memory.
2. In the host controller's 100-Hz polling loop, monitor Present Position (Register 56).
3. When position error remains within $\pm 1\,\text{count}$ for $\ge 50\,\text{ms}$, dispatch a write command to RAM Register 48 (Torque Limit) = 0 (or write the feedback integer to RAM Register 42: Goal Position).
4. If external disturbances displace the shaft by $|e| > 2\,\text{counts}$, immediately restore Register 48 = 1000 to regain active holding stiffness.
