import threading
import csv
from datetime import datetime, date
from pathlib import Path
from typing import Dict, Any, List, Optional
from pyenergyplus.api import EnergyPlusAPI
from .controller import BaseController, ControllerTimeoutError
from .logger import Logger, LOG_RUNNER_LEVEL, configure_logging
from .modeling import IDFManager, SimulationConfig


class EnergyPlusRunner:
    """
    Drive the full EnergyPlus runtime lifecycle in an isolated thread.

    This class coordinates four responsibilities:
    1. Build a runnable IDF through :class:`IDFManager`.
    2. Register timestep callbacks against the EnergyPlus Python API.
    3. Pull actions from a controller and push them into actuators.
    4. Persist monitoring data (time / observation / action) to CSV.

    The runner is intentionally controller-agnostic. Any implementation of
    :class:`BaseController` can be injected to support empty run, rule-based
    control, or queue-driven DRL interaction.

    Example:
        >>> from server.controller import EmptyController
        >>> from server.modeling import SimulationConfig
        >>> cfg = SimulationConfig.from_dict({...})
        >>> runner = EnergyPlusRunner(cfg, EmptyController())
        >>> runner.start()
        >>> runner.stop()
    """

    def __init__(
        self,
        config: SimulationConfig,
        controller: BaseController,
        log_file_path: Optional[str] = None,
        monitor_path: Optional[str] = None,
        stream_buffer: Optional[Any] = None,
    ):
        self.config = config
        self.controller = controller
        self.log_file_path = log_file_path
        self.monitor_path_override = monitor_path
        self.stream_buffer = stream_buffer

        # Configure logging - if log_file_path is provided, use it, otherwise use output_path/framework.log
        if self.log_file_path:
            configure_logging(
                self.log_file_path, enable_file_logging=self.config.output_log
            )
        else:
            configure_logging(
                self.config.output_path, enable_file_logging=self.config.output_log
            )

        self.logger = Logger().getLogger("EPLUS_RUNNER", LOG_RUNNER_LEVEL)

        # EnergyPlus API and state management
        self.api = EnergyPlusAPI()
        self.state = None
        self.thread = None
        self.simulation_complete = False
        self.handlers_initialized = False
        self.monitor_file_path: Optional[Path] = None
        self.monitor_file = None
        self.monitor_writer = None
        self.actuator_names = list(self.config.actuators.keys())

        self.var_handles: Dict[str, int] = {}
        self.meter_handles: Dict[str, int] = {}
        self.actuator_handles: Dict[str, int] = {}

        self.obs = {}
        self.first_step = True
        self.failed = False
        self.stop_requested = False
        self.failure_reason = ""

        # Progress tracking
        self.total_steps = self._calculate_total_steps()
        self.current_step = 0
        self.last_progress_time = datetime.now()
        self.progress_throttle_seconds = (
            30  # Print progress every 30 seconds to avoid spamming console
        )

    def _calculate_total_steps(self) -> int:
        """Calculate total expected simulation steps from RunPeriod."""
        if not self.config.runperiod_start or not self.config.runperiod_end:
            return 0
        try:
            start = date.fromisoformat(self.config.runperiod_start)
            end = date.fromisoformat(self.config.runperiod_end)
            # EnergyPlus RunPeriod is inclusive
            delta = end - start
            days = delta.days + 1
            if days <= 0:
                return 0
            # Total steps = days * 24 * steps_per_hour
            return days * 24 * self.config.timesteps_per_hour
        except ValueError:
            return 0

    def start(self):
        """Prepare model/output resources and start the simulation thread."""
        self.simulation_complete = False
        self.handlers_initialized = False
        self.first_step = True
        self.failed = False
        self.stop_requested = False
        self.failure_reason = ""

        # Reset progress tracking
        self.current_step = 0
        self.last_progress_time = datetime.now()

        # Configure logging - if log_file_path is provided, use it, otherwise use output_path/framework.log
        if self.log_file_path:
            configure_logging(
                self.log_file_path, enable_file_logging=self.config.output_log
            )
        else:
            configure_logging(
                self.config.output_path, enable_file_logging=self.config.output_log
            )

        idf_manager = IDFManager(self.config)
        self.modified_idf_path = idf_manager.prepare_simulation()
        # Prepare monitor output file for logging timestep data
        self._prepare_monitor_output()

        # Start the simulation thread – EnergyPlus runs are usually time-consuming
        self.thread = threading.Thread(target=self._run_energyplus, daemon=True)
        self.thread.start()
        self.logger.info("EnergyPlus simulation thread started.")

    def stop(self):
        """Request stop and wait for the runtime thread to exit gracefully."""
        self._request_runtime_stop()
        # Wait for the simulation thread to complete or timeout
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=self.config.shutdown_timeout_seconds)
            if self.thread.is_alive():
                self.logger.warning("Simulation thread did not stop within timeout.")
        self.logger.info("EnergyPlus simulation thread stopped.")

    def _run_energyplus(self):
        """Execute the EnergyPlus process and finalize runtime resources."""
        try:
            self.state = self.api.state_manager.new_state()
            # Initialize EnergyPlus API handlers for timestep callbacks
            self.api.runtime.set_console_output_status(self.state, False)
            self.api.runtime.callback_end_zone_timestep_after_zone_reporting(
                self.state, self._step_callback
            )
            cmd_args = self._make_eplus_args()
            self.logger.info(f"Running EnergyPlus with args: {cmd_args}")
            exit_code = self.api.runtime.run_energyplus(self.state, cmd_args)
            # Thread blocks, waiting for EnergyPlus simulation to complete
            if exit_code != 0 and not self.stop_requested:
                self.logger.error(
                    f"EnergyPlus simulation failed with exit code {exit_code}"
                )
                self.failed = True
                self.failure_reason = f"runtime_exit_{exit_code}"
        except Exception as e:
            self.logger.error(f"Error running EnergyPlus: {e}")
            self.failed = True
            self.failure_reason = "runner_exception"
        finally:
            self.controller.on_stop()
            self.simulation_complete = True
            self._close_monitor_output()
            if self.state:
                # Clean up EnergyPlus state after simulation completion
                self.api.state_manager.delete_state(self.state)
                self.state = None

    def _make_eplus_args(self) -> List[str]:
        """Build command arguments passed to ``run_energyplus``."""
        # Pass weather file, output directory, and modified IDF path to EnergyPlus
        return [
            "-w",
            self.config.weather_path,
            "-d",
            self.config.output_path,
            self.modified_idf_path,
        ]

    def _step_callback(self, state_argument):
        """
        Main control loop callback executed every zone timestep.

        Execution order:
        1. Lazy-initialize handles when API data becomes ready.
        2. Skip warmup timesteps.
        3. Build current observation dictionary.
        4. Query controller action.
        5. Apply actuators and record one monitor row.
        """
        if self.simulation_complete:
            return

        # At the very beginning EnergyPlus runs "dummy" timesteps while API data is not ready;
        # attempting to fetch handles at this point would crash the program. Initialize handles once ready.
        if not self.handlers_initialized:
            if self.api.exchange.api_data_fully_ready(state_argument):
                self._init_handlers(state_argument)
            else:
                return
        # Skip warmup timesteps; only log data after warmup is finished
        if self.api.exchange.warmup_flag(state_argument):
            return
        # After warmup ends, initialize the controller
        if self.first_step:
            self.controller.on_start({"variables": self.config.variables})
            self.first_step = False

        self.obs = self._get_observation(state_argument)

        try:
            action = self.controller.get_action(state_argument, self.obs)
        except ControllerTimeoutError as exc:
            self.logger.error(f"Controller timeout: {exc}")
            self.failed = True
            self.failure_reason = "controller_timeout"
            self._request_runtime_stop()
            return
        except Exception as exc:
            self.logger.error(f"Controller failed: {exc}")
            self.failed = True
            self.failure_reason = "controller_exception"
            self._request_runtime_stop()
            return
        # Write control commands and apply them to EnergyPlus
        action_map = self._set_actuators(state_argument, action)

        # Update progress
        self.current_step += 1
        if self.total_steps > 0:
            now = datetime.now()
            if (
                now - self.last_progress_time
            ).total_seconds() > self.progress_throttle_seconds:
                pct = (self.current_step / self.total_steps) * 100.0
                print(
                    f"Simulation Progress: {pct:.1f}% ({self.current_step}/{self.total_steps})"
                )
                self.last_progress_time = now

        self._record_monitor_row(state_argument, action_map)

    def _init_handlers(self, state_argument):
        """Resolve EnergyPlus handles for configured variables/meters/actuators."""
        # Variables
        for name, (var_name, key) in self.config.variables.items():
            handle = self.api.exchange.get_variable_handle(
                state_argument, var_name, key
            )
            if handle == -1:
                self.logger.warning(
                    f"Could not get handle for variable: {name} ({var_name}, {key})"
                )
            else:
                self.var_handles[name] = handle

        # Meters
        for name, meter_name in self.config.meters.items():
            handle = self.api.exchange.get_meter_handle(state_argument, meter_name)
            if handle == -1:
                self.logger.warning(
                    f"Could not get handle for meter: {name} ({meter_name})"
                )
            else:
                self.meter_handles[name] = handle

        # Actuators
        for name, (
            component_type,
            control_type,
            actuator_key,
        ) in self.config.actuators.items():
            handle = self.api.exchange.get_actuator_handle(
                state_argument, component_type, control_type, actuator_key
            )
            if handle == -1:
                self.logger.warning(
                    f"Could not get handle for actuator: {name} ({component_type}, {control_type}, {actuator_key})"
                )
            else:
                self.actuator_handles[name] = handle

        self.handlers_initialized = True
        self.logger.info("Handlers initialized.")

    def _get_observation(self, state_argument) -> Dict[str, float]:
        """Fetch all configured variable and meter values into a flat dict."""
        obs = {}
        for name, handle in self.var_handles.items():
            obs[name] = self.api.exchange.get_variable_value(state_argument, handle)
        for name, handle in self.meter_handles.items():
            obs[name] = self.api.exchange.get_meter_value(state_argument, handle)
        return obs

    def _set_actuators(self, state_argument, action: List[float]) -> Dict[str, float]:
        """
        Write controller outputs into actuator handles.

        Returns a mapping of actuator name -> written value, which is used by
        monitor CSV output to keep action traces aligned with observations.
        """
        if len(action) != len(self.actuator_names):
            if len(action) > 0:
                self.logger.warning(
                    f"Action length {len(action)} does not match actuators count {len(self.actuator_names)}"
                )
            return {}

        action_map: Dict[str, float] = {}
        for i, name in enumerate(self.actuator_names):
            if name in self.actuator_handles:
                handle = self.actuator_handles[name]
                value = action[i]
                # Set actuator value into EnergyPlus
                self.api.exchange.set_actuator_value(state_argument, handle, value)
                action_map[name] = float(value)
        return action_map

    def _request_runtime_stop(self) -> None:
        """Mark stop flags and notify EnergyPlus runtime if state exists."""
        self.simulation_complete = True
        self.stop_requested = True
        if self.state:
            try:
                self.api.runtime.stop_simulation(self.state)
            except Exception:
                pass

    def _prepare_monitor_output(self) -> None:
        """Create monitor CSV writer when CSV output is enabled."""
        if not self.config.output_csv:
            return
        output_dir = Path(self.config.output_path)
        output_dir.mkdir(parents=True, exist_ok=True)
        self._rotate_monitor_files(output_dir)
        # timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        if self.monitor_path_override:
            self.monitor_file_path = Path(self.monitor_path_override)
        else:
            self.monitor_file_path = output_dir / "monitor.csv"

        self.monitor_file = self.monitor_file_path.open(
            "w", newline="", encoding="utf-8"
        )
        self.monitor_writer = csv.DictWriter(
            self.monitor_file, fieldnames=self._monitor_fieldnames()
        )
        self.monitor_writer.writeheader()

    def _close_monitor_output(self) -> None:
        """Close monitor file handle and reset writer references."""
        if self.monitor_file:
            self.monitor_file.close()
            self.monitor_file = None
            self.monitor_writer = None

    def _rotate_monitor_files(self, output_dir: Path) -> None:
        """Delete oldest monitor CSV files based on ``max_keep_files``."""
        # Keep at least one file, even if max_keep_files is 0
        files = sorted(
            output_dir.glob("monitor_*.csv"), key=lambda p: p.stat().st_mtime
        )
        # Delete files until max_keep_files is reached
        max_keep = max(1, self.config.max_keep_files)
        while len(files) >= max_keep:
            oldest = files.pop(0)
            try:
                oldest.unlink()
            except OSError:
                break

    def _monitor_fieldnames(self) -> List[str]:
        """Return monitor CSV column order used by ``_record_monitor_row``."""
        return (
            ["step", "month", "day_of_month", "hour", "minute"]
            + list(self.config.variables.keys())
            + list(self.config.meters.keys())
            + self.actuator_names
        )

    def _record_monitor_row(self, state_argument, action_map: Dict[str, float]) -> None:
        """Append one simulation timestep row to monitor CSV output."""
        # Collect time, observation, and action data for monitor row
        row: Dict[str, Any] = {
            "step": self.current_step,
            "month": self._get_exchange_time_value("month", state_argument),
            "day_of_month": self._get_exchange_time_value(
                "day_of_month", state_argument
            ),
            "hour": self._get_exchange_time_value("hour", state_argument),
            "minute": self._get_exchange_time_value("minutes", state_argument),
        }
        for key in self.config.variables.keys():
            row[key] = self.obs.get(key)
        for key in self.config.meters.keys():
            row[key] = self.obs.get(key)
        for key in self.actuator_names:
            row[key] = action_map.get(key)

        # Write row to monitor CSV file if enabled
        if self.monitor_writer:
            self.monitor_writer.writerow(row)
            self.monitor_file.flush()

        # Push to stream buffer if configured
        if self.stream_buffer is not None:
            self.stream_buffer.append(row)

    def _get_exchange_time_value(
        self, method_name: str, state_argument
    ) -> Optional[float]:
        """Safely read a time-like value from EnergyPlus exchange API."""
        method = getattr(self.api.exchange, method_name, None)
        if callable(method):
            try:
                return method(state_argument)
            except Exception:
                return None
        return None
