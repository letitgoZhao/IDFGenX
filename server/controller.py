from abc import ABC, abstractmethod
from threading import Event
from typing import List, Dict, Any, Callable
from queue import Queue, Empty, Full


class ControllerTimeoutError(RuntimeError):
    """Raised when queue-based controller I/O exceeds configured timeout."""

    pass


class BaseController(ABC):
    """
    Controller contract consumed by :class:`EnergyPlusRunner`.

    Implementations should keep ``get_action`` lightweight and deterministic
    with respect to input observation whenever possible. Long blocking work
    should use bounded waiting and explicit timeout handling.

    Example:
        >>> class MyController(BaseController):
        ...     def on_start(self, env_info): pass
        ...     def get_action(self, state, obs): return [24.0]
        ...     def on_stop(self): pass
    """

    @abstractmethod
    def on_start(self, env_info: Dict[str, Any]) -> None:
        """Hook invoked once when simulation starts and first step is ready."""
        pass

    @abstractmethod
    def get_action(self, state: Any, obs: Dict[str, Any]) -> List[float]:
        """Called at each simulation step to get control actions.

        Args:
            state: The current EnergyPlus state object.
            obs: The current observation dictionary.

        Returns:
            List of actuator values to set.
        """
        pass

    def on_stop(self) -> None:
        """Hook invoked when runtime exits or is explicitly stopped."""
        pass


class EmptyController(BaseController):
    """
    No-op controller for baseline simulations without external control.

    This controller always returns an empty action list, so no actuator value
    is overridden by Python-side logic.
    """

    def on_start(self, env_info: Dict[str, Any]) -> None:
        pass

    def get_action(self, state: Any, obs: Dict[str, Any]) -> List[float]:
        return []


class CallbackController(BaseController):
    """
    Adapter that delegates control logic to a plain Python callback.

    Example:
        >>> def rule(state, obs):
        ...     return [22.0 if obs.get("zone_temp", 24.0) > 25.0 else 26.0]
        >>> controller = CallbackController(rule)
    """

    def __init__(self, control_callback: Callable[[Any, Dict[str, Any]], List[float]]):
        self.control_callback = control_callback

    def on_start(self, env_info: Dict[str, Any]) -> None:
        pass

    def get_action(self, state: Any, obs: Dict[str, Any]) -> List[float]:
        return self.control_callback(state, obs)


class QueueController(BaseController):
    """
    Queue-based controller for thread-safe interaction with Gym/DRL loops.

    Dataflow:
    - Push observation into ``obs_queue``.
    - Wait for next action from ``act_queue``.
    - Convert incoming action payload into ``List[float]`` for runner usage.

    ``None`` action is treated as a stop signal.
    """

    def __init__(
        self,
        obs_queue: Queue,
        act_queue: Queue,
        action_timeout: float = 30.0,
        queue_put_timeout: float = 5.0,
    ):
        self.obs_queue = obs_queue
        self.act_queue = act_queue
        self.action_timeout = action_timeout
        self.queue_put_timeout = queue_put_timeout
        self.stop_event = Event()

    def on_start(self, env_info: Dict[str, Any]) -> None:
        """Reset stop state before simulation begins."""
        self.stop_event.clear()

    def get_action(self, state: Any, obs: Dict[str, Any]) -> List[float]:
        """Exchange one observation-action pair through queues with timeouts."""
        if self.stop_event.is_set():
            return []
        try:
            self.obs_queue.put(obs, timeout=self.queue_put_timeout)
        except Full as exc:
            raise ControllerTimeoutError("Observation queue is full") from exc

        try:
            action = self.act_queue.get(timeout=self.action_timeout)
        except Empty as exc:
            raise ControllerTimeoutError("Timed out waiting for action") from exc

        if action is None:
            self.stop_event.set()
            return []
        if isinstance(action, tuple):
            return list(action)
        if isinstance(action, list):
            return action
        return [float(action)]

    def on_stop(self) -> None:
        """Signal stop and attempt to unblock observation consumer."""
        self.stop_event.set()
        try:
            self.obs_queue.put(None, timeout=self.queue_put_timeout)
        except Full:
            pass
