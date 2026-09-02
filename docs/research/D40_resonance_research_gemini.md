# Research Report: Diagnostics and Mitigation of Load-Dependent Settling Oscillations in Geared Serial-Bus Servos

**Source:** deep-research response from Gemini, 2 September 2026, run against
the same prompt as `D40_resonance_research_claude.md` (see D48 in
`docs/backlog/D.md` for context). **Pasted content was cut at a 50,000
character limit mid-way through the "Actionable Experimental Protocol"
section (Experiment 1 begins and is not complete)** — kept as received;
do not treat the missing tail as absent evidence, re-fetch if the full
protocol is needed. Kept verbatim as the reasoning is the record — do not
edit in place; correct or supersede in D48/D40's own entries instead.

## Introduction

The integration of low-cost, high-torque serial-bus servos into flexible robotic manipulators frequently introduces complex nonlinear dynamics that compromise positional accuracy and system stability. This report investigates the specific phenomenon of sustained, low-amplitude settling oscillations—commonly classified in control theory as limit cycles—observed in a geared rotary joint driven by a Waveshare/Feetech STS3215 servo. The system architecture incorporates a 12-bit magnetic encoder (4096 counts per revolution), a 44:30 toothed timing belt reduction yielding a transmission ratio of 1.4667, and a Zephyr-based microcontroller issuing absolute position commands via the vendor-specific WritePosEx protocol. To eliminate backlash-driven positional ambiguity, the controller utilizes a unidirectional positioning strategy consisting of a 1.5° deliberate overshoot followed by a final return approach.

Empirical testing under a hand-applied proxy load has revealed a highly intermittent, position-dependent oscillation during the final settling phase. The servo output shaft exhibits a sustained positional bounce within a 0.06° to 0.24° band (1 to 4 raw encoder steps) that occasionally fails to damp out entirely within a 15-second observation window. The application of external physical damping suppresses the oscillation, and tuning adjustments to the proportional position gain (P) and the static friction breakaway threshold (MinStartForce) have yielded non-monotonic, inconsistent results.

The primary investigative hypothesis posits that this behavior is driven by load-coupled mechanical resonance rather than simple Coulomb friction or stick-slip dynamics. To validate this hypothesis and provide a comprehensive mitigation strategy, this analysis synthesizes established control-theoretic principles concerning two-mass elastic systems, digital signal processing limitations, documented practitioner data from the open-source LeRobot community, and the dynamic consequences of trajectory shaping in compliant transmissions.

## Differential Diagnostics: Mechanical Resonance Versus Coulomb Friction

In closed-loop servomechanisms, sustained oscillations around a commanded setpoint indicate the presence of a limit cycle. A limit cycle is an isolated, closed trajectory in the phase plane of a nonlinear dynamic system, meaning the system continuously oscillates with a fixed amplitude and period. In small, geared, belt-driven systems, limit cycles are predominantly induced by two distinct nonlinearities: the stick-slip friction phenomenon driven by the Stribeck effect, and load-coupled mechanical resonance driven by finite transmission stiffness and inertia mismatch. Distinguishing between these two root causes is the foundational step in system tuning, as their respective control remedies are often mutually exclusive.

### Stick-Slip Friction and the Stribeck Effect

Coulomb friction imposes a nonlinear resistance to motion that is independent of velocity but highly discontinuous at the zero-velocity crossing. In practical mechanical assemblies involving gears and bearings, this is complicated by the Stribeck effect, a tribological phenomenon where the static friction (stiction) is significantly higher than the kinetic friction experienced once motion begins.

When a servo control loop—particularly one with an integral term or a high proportional gain responding to a small persistent error—attempts to correct a minute position deficit, the control effort (torque) gradually increases until it exceeds the breakaway stiction force. The moment physical motion initiates, the opposing friction drops precipitously to the kinetic level. The control effort that was necessary to break stiction is suddenly excessive for the kinetic state, causing the motor to accelerate rapidly and overshoot the target setpoint. The motor subsequently decelerates, crosses the zero-velocity point, and stiction re-engages. The controller then builds torque in the opposite direction, and the cycle repeats ad infinitum, producing a deterministic "stick-slip" relaxation oscillator limit cycle.

### Load-Coupled Mechanical Resonance in Two-Mass Systems

Conversely, a servo driving a load through a compliant element, such as a toothed timing belt, is classically modeled in control theory as a "two-mass system." The motor rotor and the primary driving pulley constitute the first mass with inertia J_m, the output arm and driven pulley constitute the second mass with inertia J_l, and the timing belt provides a finite torsional stiffness K and a viscous damping coefficient C.

In a two-mass system, the mechanical compliance interacts with the dual inertias to create a resonant frequency (ω_r) and an anti-resonant frequency (ω_a). The natural resonant frequency of the coupled system is governed by the equation ω_r = √(K · (J_m + J_l) / (J_m · J_l)). When the bandwidth of the servo's closed-loop position or velocity controller overlaps with this resonant frequency, the control loop inadvertently injects energy into the elastic mode of the belt, sustaining a harmonic limit cycle.

The analytical technique most frequently used to predict these oscillations is Describing Function Analysis. The describing function method approximates nonlinearities—such as deadbands, backlash, and friction—as amplitude-dependent complex gains. By plotting the negative inverse of the describing function against the linear system's Nyquist plot, engineers can identify intersections that mathematically predict the existence, amplitude, and frequency of a limit cycle. When describing function analysis is applied to a two-mass system with a compliant belt and a high-gain controller, it reliably demonstrates that even minimal phase lag in the feedback loop can destabilize the elastic mode, leading to sustained oscillations.

### Evaluating the Diagnostic Signatures

| Diagnostic Signature | Expectation for Stick-Slip Friction | Expectation for Mechanical Resonance | Alignment with Empirical Data |
|---|---|---|---|
| Positional Dependency | Amplitude is independent of joint angle, dictated entirely by constant gear mesh friction. | Severity changes with position, as the effective load inertia (J_l) varies with the lever arm and gravitational vector, shifting the resonant frequency. | **Matches Resonance**: The worst-case oscillation occurred exclusively at the −60° position, indicating an inertia-dependent modal shift. |
| Response to Tuning Sweeps | Monotonic. Altering MinStartForce directly shifts the breakaway threshold, leading to a predictable increase or decrease in the limit cycle. | Non-Monotonic. Tuning P-gains alters the phase margin and bandwidth. Intermediate gains may inadvertently align the control bandwidth with the resonant peak. | **Matches Resonance**: Sweeping MinStartForce from 0 to 200 yielded highly non-monotonic results; intermediate values (100, 150) were mixed, while extremes behaved differently. |
| Intermittency and Phase | Highly deterministic. If the error threshold exceeds the friction band, the stick-slip cycle will trigger consistently. | Highly intermittent. Resonance requires energy injection at a specific phase relative to the belt's natural frequency. | **Matches Resonance**: A 40–60% failure rate across identical repeated trials is a hallmark of phase-sensitive resonant excitation. |
| Physical Damping | Adding load/damping generally worsens stick-slip by increasing the disparity between static and kinetic friction. | Adding physical damping increases the viscous damping ratio (ζ), absorbing kinetic energy and stabilizing the control loop. | **Matches Resonance**: Anecdotal and controlled tests confirmed that placing a hand on the output shaft reliably suppressed the oscillation. |

Based on these specific deviations from standard stick-slip behavior, the working hypothesis that the system is experiencing a load-induced resonant limit cycle is mathematically and practically sound.

## The Epistemological Limits of Low-Frequency Signal Acquisition

A critical constraint in the current diagnostic methodology is the reliance on raw position data polled over the serial bus at intervals of 80 to 150 milliseconds, corresponding to a sampling rate of roughly 6.6 Hz to 12.5 Hz. In the context of digital signal processing and vibration analysis, this sampling rate is fundamentally inadequate for characterizing the kinetic reality of a mechanical limit cycle due to the Nyquist-Shannon sampling theorem and the resulting phenomenon of signal aliasing.

According to the Nyquist-Shannon theorem, an analog signal must be sampled at a rate (F_s) strictly greater than twice its highest frequency component (F_max) to be accurately reconstructed without distortion. This boundary is known as the Nyquist frequency (F_s/2). Mechanical limit cycles in small, geared DC servo systems typically exhibit oscillation frequencies in the 5 Hz to 40 Hz range, depending on the stiffness of the transmission and the mass of the load.

When a system oscillates at a frequency higher than the Nyquist frequency, the sampling process folds the high-frequency kinetic energy down into the lower frequency spectrum, creating a false "alias" signal. For example, if the STS3215 servo and belt transmission are physically resonating at a true frequency of 12 Hz, sampling the position register at a strict 10 Hz rate will yield a Nyquist frequency of 5 Hz. The 12 Hz signal will alias down, appearing in the data logs as a smooth, low-frequency oscillation of exactly 2 Hz (calculated as |12−10|=2).

Because the data acquisition methodology is severely undersampled, the 10 Hz position-versus-time logs present a distorted, artificially smoothed representation of the shaft's motion. This aliasing effect completely masks the high-frequency transients, harmonics, and vibration waveforms necessary to definitively diagnose the root cause of the limit cycle via Fourier analysis.

### Required Diagnostic Modalities

To differentiate the broad harmonic spectrum of a discontinuous stick-slip breakaway from the sharp, singular frequency peak of a harmonic resonance, engineering teams cannot rely on low-frequency position polling. The standard diagnostic approach in motion control requires:

- **High-Frequency Feedback Acquisition:** The servo's internal Present_Speed (Register 58) or Present_Position (Register 56) must be polled at a minimum of 200 Hz to capture oscillations up to 100 Hz accurately.
- **Torque and Current Spectrum Analysis:** The most reliable indicator of control-loop resonance is the Fast Fourier Transform (FFT) of the motor's current command, which is directly proportional to torque. Identifying a sharp peak in the frequency spectrum of the Present_Load (Register 60) or Present_Current (Register 69) during the settling phase definitively confirms that the control loop is amplifying a specific mechanical resonance.

## Standard Remediation for Load-Induced Resonance

When a geared, belt-driven servomechanism exhibits load-coupled resonance, the control engineering discipline utilizes a hierarchy of remedies categorized into mechanical plant alterations, feedback loop attenuation, and feedforward trajectory shaping.

### Mechanical Mitigation Strategies

The most robust solution to a two-mass resonance problem is to alter the physical plant to increase the resonant frequency, pushing it safely above the operational bandwidth of the servo's control loop.

- **Inertia Matching Optimization:** The severity of resonance in a two-mass system is dictated by the inertia ratio (λ = J_l/J_m). If the load inertia is vastly larger than the motor inertia, the motor struggles to dictate the dynamics of the load across the compliant interface. The current timing belt reduction ratio of 44:30 (1.4667) squares the reflected inertia to approximately 2.15. This is a very low reduction ratio for a robotic arm; increasing the mechanical advantage (e.g., to 3:1 or 5:1) would reduce the reflected inertia quadratically, vastly improving the inertia ratio and shifting the resonant frequency higher.
- **Increasing Transmission Stiffness:** The timing belt acts as a torsional spring. Upgrading to a wider belt, utilizing a steel-core or Kevlar-reinforced belt, or transitioning entirely to a rigid coupling (such as a zero-backlash harmonic drive) linearly increases the torsional stiffness (K). A stiffer transmission minimizes the phase lag between the motor and the load, preventing the controller from overcompensating during the transient settling phase.
- **Passive Damping Additions:** The introduction of passive energy dissipation directly stabilizes the system. Incorporating a rotary viscous damper, a tuned mass damper, or localized friction elements at the output shaft removes the kinetic energy from the secondary mass before it can reflect back across the belt to the motor's encoder, precisely mimicking the stabilizing effect of the hand-damping test.

### Control-Theoretic Mitigation Strategies

When physical mechanical alterations are unfeasible, the servo's internal control logic must be adjusted to ignore or suppress the resonant dynamics.

- **Bandwidth Reduction (De-Tuning):** In standard industrial practice, lowering the position proportional gain (P) and increasing the velocity loop damping is the primary defense against resonance. However, reducing the P-gain inherently decreases the static stiffness of the joint. As observed during testing, lowering the P-gain from 32 to 16 suppressed the high-frequency trembling but introduced a steady-state droop of 0.17°, indicating the controller no longer possessed the bandwidth or authority to overcome the static friction of the gear train.
- **Digital Notch Filtering:** High-end industrial servo drives employ digital notch filters in the torque or velocity command paths. These filters are tuned to sharply attenuate signals exactly at the system's identified resonant frequency, preventing the controller from injecting energy into the elastic mode without sacrificing overall bandwidth. Unfortunately, hobbyist and prosumer servos such as the Feetech STS/SCS family lack the digital signal processing architecture to support user-configurable notch filters.
- **Deadband Injection:** As evidenced by the testing data, increasing the CW/CCW Dead Zone (Registers 0x1A/0x1B) partially mitigates the oscillation by establishing a positional window where the controller outputs zero torque, severing the feedback loop that sustains the limit cycle. This represents a direct compromise, trading dynamic stability for a guaranteed degradation in steady-state accuracy (yielding the observed ±0.12–0.24° final position error).

## Advanced Capabilities of the Feetech STS3215 Architecture

The research request indicates that the tuning effort has been strictly confined to Proportional (P), Integral (I), Derivative (D), MinStartForce, and the CW/CCW dead zone. A comprehensive review of the Feetech STS3215 SRAM control table, augmented by practitioner data from the open-source LeRobot community—which utilizes this exact servo extensively for compliant manipulators like the SO-100 and SO-101—reveals critical, underutilized registers that govern motion profiling. The failure to exploit these registers is highly likely the root cause of the controller's inability to settle the load gracefully.

### The Role of Internal Trajectory Generation

The most significant omission in the current control protocol is the failure to constrain the derivative kinematic variables (velocity and acceleration) of the trajectory. According to the STS3215 memory map, the servo supports an internal trapezoidal motion profile generator, which regulates how aggressively the motor attempts to reach a new position setpoint.

| SRAM Register Name | Address (Hex) | Address (Dec) | Size | Description and Scaling Unit |
|---|---|---|---|---|
| Acceleration | 0x29 | 41 | 1 Byte | Limits the acceleration and deceleration rate of the internal trajectory planner. The unit is 100 steps/sec². |
| Goal_Speed | 0x2E (L), 0x2F (H) | 46, 47 | 2 Bytes | Limits the maximum velocity of the commanded move. The unit is 50 steps/sec. |

Resonance is fundamentally excited by high-frequency components in the reference command. A standard step-input command (telling the servo to instantly move 1.5° away) contains infinite frequency harmonics, acting as a kinetic hammer strike on the compliant belt. By utilizing strict acceleration and deceleration limits, the motion profile becomes trapezoidal or S-curve shaped. This mathematically acts as a low-pass filter on the command trajectory, ensuring that no sudden jerks inject resonant energy into the secondary mass during the critical final approach.

### Practitioner Insights from the LeRobot Community

The open-source robotics community has extensively documented the challenges of using Feetech STS3215 servos in flexible joint configurations. Analysis of LeRobot GitHub repositories and issue trackers reveals that these servos often exhibit extreme jitter, cross-coupling instability, and extreme sensitivity during small positional updates when acceleration and velocity limits are not strictly defined.

In the development of the SO-101 arm, users reported severe "wrist roll" instability and unwanted resonance triggered by the movement of adjacent joints. The community found that the factory default P-gain of 32 is excessively high for a manipulator handling an external load. Standard LeRobot configurations drastically reduce the P-coefficient (often down to 16, 4, or even 2) while implementing deadzone filtering.

Crucially, users reported that the STS3215 servos on the SO-101 arm frequently exhibited erratic behavior or failed to execute smooth motions until goal_velocity and goal_acceleration were explicitly enforced in the Python control scripts.

The Zephyr microcontroller governing this system utilizes the WritePosEx vendor command. The signature for this function takes explicit parameters for Position, Speed, and Acceleration. If the overshoot and final return legs are currently being commanded with maximum or unconstrained speed and acceleration arguments, the servo will attempt to reach the target with maximum instantaneous torque, violently exciting the belt's compliance. By configuring Register 0x29 (Acceleration) to a moderate value (e.g., 10 to 20, corresponding to 1000–2000 steps/sec²), the servo's internal trajectory generator will seamlessly ramp the torque up and down during the final 1.5° approach, gently bringing the load to rest without triggering the elastic rebound.

**Note added by the servo_mvp session that ran this research:** this project's own `_command()` (`python/app/services/motion_service.py`) already passes a moderate, non-zero, non-maximum acceleration (`kDefaultAcceleration=50` from `sketch/src/Config.h`, i.e. ~5,000 steps/s² in the servo's own unit) on every move including the fine-approach final leg — Gemini's assumption of "maximum or unconstrained" acceleration on this project specifically has not been verified and may not hold; confirm the actual value in flight before assuming this is the mechanism. `fine_approach_final_acceleration` (a config override for the final leg specifically, lower than the move's own acceleration) was built in D40c and never used — this is the concrete, already-available lever to test Gemini's recommendation with.

## The Dynamic Consequences of Unidirectional Anti-Backlash Positioning

To counteract the mechanical slop in the 44:30 gear and belt reduction, the control software employs a "fine approach" anti-backlash mechanism. Every command is split into an overshoot leg (passing the target by 1.5°) followed by a final return leg to the true target. This strategy—unidirectional positioning—ensures the gear train is always loaded against the same flank of the gear teeth, eliminating positional ambiguity caused by the deadband.

While unidirectional positioning is the gold standard for rigidly coupled machine tools (such as CNC mills utilizing ball screws), it is fundamentally antagonistic to compliant, belt-driven systems susceptible to two-mass resonance.

### The Transient Shock of Reversal

When the STS3215 servo executes the 1.5° overshoot and subsequently commands a reversal for the final leg, the system must undergo a violent transition in kinetic energy. The motor must shed the kinetic energy of the load, pass through the zero-velocity point, traverse the physical backlash gap (where the motor rotor briefly disconnects from the load inertia), and forcefully re-engage the load in the opposite direction.

This mechanical sequence creates an acute torque transient. When the gears re-engage after traversing the backlash gap, the impact acts as an impulse function. In frequency domain analysis, a pure impulse contains all frequencies simultaneously. Therefore, the re-engagement impact guarantees the excitation of the belt's natural resonant frequency. Furthermore, because the final return leg is exceptionally short (1.5°), the servo operates entirely within its transient acceleration and deceleration phases, maximizing phase lag and driving the system directly into a limit cycle.

### Control-Theoretic Alternatives to Deliberate Overshoot

In flexible robotics, deliberate positional overshoot is actively avoided because it destabilizes the state-space dynamics of the load. Better-established alternatives for managing backlash in compliant systems include:

| Backlash Mitigation Strategy | Mechanism of Action | Suitability for Compliant STS3215 Systems |
|---|---|---|
| Model-Based Backlash Compensation (Extended State Observers) | Instead of a physical overshoot move, the controller uses an Extended State Observer (ESO) to mathematically estimate the backlash width. The controller injects a brief, highly calibrated pulse of velocity strictly to traverse the gap without moving the load, then resumes standard PID tracking. | Moderate: the STS3215 does not support ESOs internally, but this logic can be executed externally by the Zephyr microcontroller by analyzing the commanded vs. actual position differential. |
| Input Shaping (Zero Vibration Derivatives) | Convolving the target command with a sequence of impulses timed specifically to exactly cancel out the residual vibration of the flexible mode (e.g., ZVD or Extra Insensitive shapers). | High: if the resonant frequency can be identified, the final leg can be split into two discrete micro-steps timed half a vibrational period apart, leading to destructive interference of the resonance. |
| Trajectory Blending with S-Curve Deceleration | Path planning algorithms are structured so the robot only approaches from the preferred direction when globally optimal. If a reversal is mandatory, the deceleration profile is severely extended over a long temporal window to gently bridge the backlash gap without a hard stop-and-reverse. | High: by relying heavily on the Acceleration (0x29) register during reversals, the transient shock of re-engagement is smoothed, preventing the broadband impulse that triggers the limit cycle. |
| Dual-Loop Control (Direct Load Sensing) | Placing a secondary encoder directly on the output shaft. The position loop is closed on the load, while the velocity loop is closed on the motor, enclosing the backlash within the control loop. | Low: requires significant hardware modification and custom cascaded PID loops on the microcontroller, bypassing the STS3215's internal position controller entirely. |

## The Epistemological Limitations of Proxy-Load Testing

A defining constraint of the current investigation is that all empirical testing was performed on a "bench-proxy load"—an isolated belt-and-shaft mechanism loaded manually with a hand-held weight, rather than the final robotic arm structure. The engineering team hypothesizes that testing with the actual assembly is the only definitive way to determine if the limit cycle will reproduce.

The academic literature and fundamental principles of mechanical vibration absolutely confirm this assumption; predictive mapping from a proxy load to a real, multi-link robotic arm in a resonant system is mathematically invalid.

### The Physics of Proxy Invalidity

A resonant limit cycle relies entirely on the natural frequency of the specific mechanical plant, governed by the ratio of stiffness to effective inertia (ω = √(K/J_eff)). The proxy load fails to replicate this dynamic system on three critical fronts:

- **Inertia Tensor Mismatch:** a hand-held weight applies a static gravitational torque vector and a crude approximation of mass. It fundamentally fails to replicate the moment of inertia tensor (J_eff) of a distributed, multi-link robotic arm. The rotational inertia perceived by the servo is vastly different when driving a complex geometric structure compared to a centralized point mass.
- **Variable Coriolis and Centrifugal Forces:** in the real physical arm, the effective inertia reflected to the target servo will change continuously as the distal joints (elbow, wrist) extend or retract. The bench proxy possesses a fixed mass distribution. A parameter combination (e.g., P=24, MinStartForce=150) that successfully settles the proxy load at −60° may immediately trigger a violent limit cycle on the real arm when fully extended. The increased inertia of full extension will drag the resonant frequency down directly into the controller's active bandwidth.
- **Structural Mounting Stiffness:** the testing notes describe the bench proxy as having "no rigid mount." The physical stiffness of the mount itself acts as a series spring within the two-mass model. A loosely held proxy will damp out high-frequency vibrations through the operator's hand (bio-mechanical damping) and exhibit a significantly lower aggregate structural stiffness than a rigidly bolted aluminum or carbon-fiber robotic chassis.

### Predicting Bounding Conditions

While an exact prediction of the real arm's behavior is impossible without the physical hardware, the engineering team can establish worst-case bounding conditions. By calculating the maximum possible extended moment of inertia of the final CAD arm design, the team can estimate the lowest theoretical resonant frequency of the joint. If this lowest theoretical resonant frequency remains significantly higher than the velocity-loop bandwidth of the STS3215, the real arm is unlikely to oscillate. However, given the inherently compliant nature of timing belts and the 44:30 reduction ratio—which provides minimal inertia mitigation—it is highly probable that the real arm will exhibit more severe resonance characteristics than the proxy load.

## Actionable Experimental Protocol (as received — cut off mid-section)

The sustained, position-dependent, and highly intermittent settling oscillations observed in the STS3215 servo system are unequivocally symptomatic of a load-coupled mechanical resonance limit cycle. This resonance is being severely exacerbated by the transient shock of the unidirectional anti-backlash overshoot algorithm. The current 10 Hz sampling methodology is masking the true high-frequency dynamics of the limit cycle due to signal aliasing, rendering pure position logs inadequate for spectral diagnosis. Furthermore, the utilization of a proxy weight fundamentally alters the modal mass and stiffness of the system, invalidating any fine-tuning executed on the test bench.

To resolve this issue and bridge the gap to the final robotic assembly, an engineer with access to the microcontroller and the STS3215 tuning interface should execute the following specific, sequential protocol:

**Experiment 1: Activate and Optimize the Trajectory Generator (Software)**

Relying purely on PID tuning ignores the servo's internal motion profiling capabil…

*(response was cut off here by the pasting tool's 50,000 character limit —
the rest of Gemini's own experimental protocol was not captured; re-run the
same prompt against Gemini and re-save this file, or ask Gemini directly to
continue from "Experiment 1," if the full protocol is wanted before D48 is
executed)*
