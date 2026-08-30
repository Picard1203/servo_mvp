"""Servo endpoints: state, move, stop, lock."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import (
    get_calibration_service,
    get_isolation_service,
    get_motion_service,
    get_servo_repository,
    get_state_store,
)
from app.repositories.abstract.servo_repository import ServoRepository
from app.schemas.servo import (
    CalibrationResponse,
    IsolateRequest,
    IsolateResponse,
    LockRequest,
    LockResponse,
    MoveAcceptedResponse,
    MoveRequest,
    RecoverResponse,
    ServoStateResponse,
    StopResponse,
    TorqueRegisterResponse,
)
from app.services.calibration_service import CalibrationService
from app.services.isolation_service import IsolationService
from app.services.motion_service import MotionService
from app.services.servo_state import ServoStateStore

router = APIRouter(prefix="/api/v1/servo", tags=["servo"])

MotionDep = Annotated[MotionService, Depends(get_motion_service)]
StateDep = Annotated[ServoStateStore, Depends(get_state_store)]
CalibrationDep = Annotated[CalibrationService,
                          Depends(get_calibration_service)]
IsolationDep = Annotated[IsolationService, Depends(get_isolation_service)]
ServoDep = Annotated[ServoRepository, Depends(get_servo_repository)]


@router.get("/state", response_model=ServoStateResponse)
def get_state(state: StateDep) -> ServoStateResponse:
    """Returns the full state snapshot for the client.

    Args:
        state (ServoStateStore): Injected servo state store.

    Returns:
        ServoStateResponse: Current position, flags, and telemetry.
    """
    view = state.snapshot()
    return ServoStateResponse.from_view(view)


@router.post("/move", status_code=202, response_model=MoveAcceptedResponse)
def post_move(request: MoveRequest,
              motion: MotionDep) -> MoveAcceptedResponse:
    """Starts a move toward the requested target angle.

    Args:
        request (MoveRequest): Target angle and acceleration.
        motion (MotionService): Injected motion service.

    Returns:
        MoveAcceptedResponse: Acknowledgement with accepted target angle.
    """
    motion.move_to(request.target_deg, request.acceleration)
    return MoveAcceptedResponse(accepted=True, target_deg=request.target_deg)


@router.post("/stop", response_model=StopResponse)
def post_stop(motion: MotionDep) -> StopResponse:
    """Stops the current move.

    Args:
        motion (MotionService): Injected motion service.

    Returns:
        StopResponse: Acknowledgement of stop command.
    """
    motion.stop()
    return StopResponse(stopped=True)


@router.post("/lock", response_model=LockResponse)
def post_lock(request: LockRequest,
              motion: MotionDep) -> LockResponse:
    """Changes the digital lock state.

    Args:
        request (LockRequest): Desired lock state.
        motion (MotionService): Injected motion service.

    Returns:
        LockResponse: The applied lock state.
    """
    motion.set_lock(request.locked)
    return LockResponse(locked=request.locked)


@router.post("/isolate", response_model=IsolateResponse)
def post_isolate(request: IsolateRequest,
                 isolation: IsolationDep) -> IsolateResponse:
    """Sets motor isolation intent and reconciles it immediately.

    Args:
        request (IsolateRequest): Desired isolation state.
        isolation (IsolationService): Injected isolation service.

    Returns:
        IsolateResponse: The isolation intent that was set.
    """
    isolation.set_isolated(request.isolated)
    return IsolateResponse(isolated=request.isolated)


@router.post("/calibrate", status_code=201, response_model=CalibrationResponse)
def post_calibrate(calibration: CalibrationDep) -> CalibrationResponse:
    """Captures the current physical position as the datum.

    Args:
        calibration (CalibrationService): Injected calibration service.

    Returns:
        CalibrationResponse: The stored datum.
    """
    datum = calibration.calibrate()
    return CalibrationResponse(raw_counts=datum.raw_counts,
                               captured_at=datum.captured_at)


@router.get("/diagnostics/torque_register",
            response_model=TorqueRegisterResponse)
def get_torque_register(servo: ServoDep) -> TorqueRegisterResponse:
    """Reads the servo torque-enable register directly.

    Args:
        servo (ServoRepository): Injected servo repository.

    Returns:
        TorqueRegisterResponse: Raw register value or None if read failed.
    """
    return TorqueRegisterResponse(
        torque_register=servo.read_torque_register())


@router.post("/recover", response_model=RecoverResponse)
def post_recover(motion: MotionDep) -> RecoverResponse:
    """Clears a tripped overload fault by re-commanding position.

    Args:
        motion (MotionService): Injected motion service.

    Returns:
        RecoverResponse: Acknowledgement of recovery action.
    """
    motion.recover()
    return RecoverResponse(recovered=True)
