"""Servo endpoints: state, move, stop, lock."""

from typing import Annotated

from fastapi import APIRouter, Depends

from app.deps import get_motion_service, get_state_store, get_zero_service
from app.schemas.servo import (LockRequest, LockResponse, MoveAcceptedResponse,
                               MoveRequest, RecoverResponse,
                               ServoStateResponse, StopResponse)
from app.schemas.zeros import ZeroResponse
from app.services.motion_service import MotionService
from app.services.servo_state import ServoStateStore
from app.services.zero_service import ZeroService

router = APIRouter(prefix="/api/v1/servo", tags=["servo"])

MotionDep = Annotated[MotionService, Depends(get_motion_service)]
StateDep = Annotated[ServoStateStore, Depends(get_state_store)]
ZeroDep = Annotated[ZeroService, Depends(get_zero_service)]


@router.get("/state", response_model=ServoStateResponse)
def get_state(state: StateDep) -> ServoStateResponse:
    """Returns the full state snapshot for the client.

    Args:
        state: Injected servo state store.

    Returns:
        Current position, flags and telemetry.
    """
    view = state.snapshot()
    return ServoStateResponse(
        output_deg=view.output_deg, reading_valid=view.reading_valid,
        moving=view.moving, locked=view.locked,
        settling=view.settling, position_verified=view.position_verified,
        active_zero=view.active_zero_name,
        temperature_c=view.temperature_c, voltage_v=view.voltage_v,
        current_a=view.current_a, torque_kgcm=view.torque_kgcm,
        overload=view.overload, overcurrent=view.overcurrent,
        overheat=view.overheat, voltage_fault=view.voltage_fault,
        sensor_fault=view.sensor_fault, angle_fault=view.angle_fault)


@router.post("/move", status_code=202, response_model=MoveAcceptedResponse)
def post_move(request: MoveRequest,
                    motion: MotionDep) -> MoveAcceptedResponse:
    """Starts a move; domain errors are mapped to HTTP by the app.

    Args:
        request: Target angle and speed.
        motion: Injected motion service.

    Returns:
        Acknowledgement with the accepted target.
    """
    motion.move_to(request.target_deg, request.speed_dps,
                   request.acceleration)
    return MoveAcceptedResponse(accepted=True, target_deg=request.target_deg)


@router.post("/stop", response_model=StopResponse)
def post_stop(motion: MotionDep) -> StopResponse:
    """Stops the current move.

    Args:
        motion: Injected motion service.

    Returns:
        Acknowledgement.
    """
    motion.stop()
    return StopResponse(stopped=True)


@router.post("/lock", response_model=LockResponse)
def post_lock(request: LockRequest,
                    motion: MotionDep) -> LockResponse:
    """Changes the digital lock state.

    Args:
        request: Desired lock state.
        motion: Injected motion service.

    Returns:
        The applied lock state.
    """
    motion.set_lock(request.locked)
    return LockResponse(locked=request.locked)


@router.post("/calibrate", status_code=201, response_model=ZeroResponse)
def post_calibrate(zeros: ZeroDep) -> ZeroResponse:
    """Captures the current physical position as the calibration datum.

    Call when the mechanism is physically at the documented reference
    position (install, and after any power-off). Creates or updates the
    datum zero, activates it, and marks the position verified.

    Args:
        zeros: Injected zero service.

    Returns:
        The stored datum zero.
    """
    datum = zeros.calibrate()
    return ZeroResponse(id=datum.id, name=datum.name,
                        raw_counts=datum.raw_counts,
                        is_active=datum.is_active, is_datum=datum.is_datum,
                        created_at=datum.created_at)


@router.post("/recover", response_model=RecoverResponse)
def post_recover(motion: MotionDep) -> RecoverResponse:
    """Clears a tripped overload fault by re-commanding the position.

    Args:
        motion: Injected motion service.

    Returns:
        Acknowledgement.
    """
    motion.recover()
    return RecoverResponse(recovered=True)
