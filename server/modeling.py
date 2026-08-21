import os
import json
from datetime import date
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any
from eppy.modeleditor import IDF
from .logger import Logger, LOG_MODEL_LEVEL


class SimulationConfig:
    """
    Typed configuration that defines how a simulation is executed.

    Design goals:
    - Provide a stable, validated contract between config files and runtime.
    - Keep the control/observation schema explicit for both rule and DRL modes.
    - Centralize DRL defaults while preserving user overrides.

    Example (minimal empty run):
        >>> payload = {
        ...     "building_file": "./examples/building/5ZoneAutoDXVAV.idf",
        ...     "weather_file": "./examples/weather/USA_IL_Chicago-OHare.Intl.AP.725300_TMY3.epw",
        ...     "output_path": "./output",
        ...     "mode": "empty"
        ... }
        >>> config = SimulationConfig.from_dict(payload)
    """

    def __init__(
        self,
        building_path: str,
        weather_path: str,
        output_path: str,
        env_name: str,
        mode: str = "empty",
        variables: Optional[Dict[str, Tuple[str, str]]] = None,
        meters: Optional[Dict[str, str]] = None,
        actuators: Optional[Dict[str, Tuple[str, str, str]]] = None,
        time_variables: Optional[List[str]] = None,
        output_csv: bool = True,
        output_log: bool = True,
        max_keep_files: int = 10,
        step_timeout_seconds: float = 60.0,
        queue_put_timeout_seconds: float = 5.0,
        shutdown_timeout_seconds: float = 15.0,
        drl: Optional[Dict[str, Any]] = None,
        runperiod_start: Optional[str] = None,
        runperiod_end: Optional[str] = None,
        timesteps_per_hour: int = 1,
    ):
        self.building_path = building_path
        self.weather_path = weather_path
        self.output_path = output_path
        self.env_name = env_name
        self.mode = mode
        self.variables = variables if variables is not None else {}
        self.meters = meters if meters is not None else {}
        self.actuators = actuators if actuators is not None else {}
        self.time_variables = time_variables if time_variables is not None else []
        self.output_csv = output_csv
        self.output_log = output_log
        self.max_keep_files = max_keep_files
        self.step_timeout_seconds = step_timeout_seconds
        self.queue_put_timeout_seconds = queue_put_timeout_seconds
        self.shutdown_timeout_seconds = shutdown_timeout_seconds
        self.drl = drl if drl is not None else {}
        self.runperiod_start = runperiod_start
        self.runperiod_end = runperiod_end
        self.timesteps_per_hour = timesteps_per_hour

    def validate(self) -> None:
        """Validate required fields and enforce mode-specific constraints."""
        if not self.building_path:
            raise ValueError("building_path is required")
        if not self.weather_path:
            raise ValueError("weather_path is required")
        if not self.output_path:
            raise ValueError("output_path is required")
        if self.mode not in {"empty", "rule", "drl"}:
            raise ValueError("mode must be one of: empty, rule, drl")
        # In rule or drl mode, actuators must be provided
        if self.mode in {"rule", "drl"} and not self.actuators:
            raise ValueError("rule/drl mode requires actuators")
        # In rule or drl mode, at least variables or meters must be provided
        if self.mode in {"rule", "drl"} and not (self.variables or self.meters):
            raise ValueError("rule/drl mode requires variables or meters")
        # EnergyPlus requires timesteps_per_hour to be at least 1
        if self.timesteps_per_hour < 1:
            raise ValueError("timesteps_per_hour must be >= 1")
        # step_timeout_seconds, queue_put_timeout_seconds, and shutdown_timeout_seconds must be greater than 0
        if self.step_timeout_seconds <= 0:
            raise ValueError("step_timeout_seconds must be > 0")
        if self.queue_put_timeout_seconds <= 0:
            raise ValueError("queue_put_timeout_seconds must be > 0")
        if self.shutdown_timeout_seconds <= 0:
            raise ValueError("shutdown_timeout_seconds must be > 0")
        # If runperiod_start or runperiod_end is provided, it must be a valid ISO date string
        if self.runperiod_start is not None:
            date.fromisoformat(self.runperiod_start)
        if self.runperiod_end is not None:
            date.fromisoformat(self.runperiod_end)
        self._validate_drl()

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SimulationConfig":
        """
        Build a config from a dictionary payload.

        Supports both legacy keys (building_path/weather_path) and
        preferred keys (building_file/weather_file).
        Defaults:
            env_name: 'eplus-env'
            mode: 'empty'
            output_path: './output'
        """
        env_name = data.get("env_name") or data.get("id") or "eplus-env"
        mode = data.get("mode", "empty")
        output_config = data.get("outputs", {})
        observation_config = data.get("observation", {})
        control_config = data.get("control", {})
        drl_config = cls._normalize_drl_config(data.get("drl", {}))
        if isinstance(control_config, dict):
            for key in ["action_space_type", "action_low", "action_high", "discrete_n"]:
                if key in control_config:
                    drl_config[key] = control_config[key]
            control_env_wrapper = control_config.get("env_wrapper_params")
            if isinstance(control_env_wrapper, dict):
                if not isinstance(drl_config.get("env_wrapper_params"), dict):
                    drl_config["env_wrapper_params"] = {}
                drl_config["env_wrapper_params"].update(control_env_wrapper)
        runperiod_config = data.get("runperiod", {})
        variables = cls._parse_variables(
            data.get("variables", observation_config.get("variables", {}))
        )
        meters = cls._parse_meters(
            data.get("meters", observation_config.get("meters", {}))
        )
        actuators = cls._parse_actuators(
            data.get("actuators", control_config.get("actuators", {}))
        )

        # Convert the raw config dict into a SimulationConfig instance and validate it
        output_path_raw = data.get("output_path", str(Path.cwd() / "output"))
        if "{id}" in output_path_raw:
            output_path_raw = output_path_raw.replace("{id}", env_name)

        repo_root = Path(__file__).resolve().parent.parent

        building_raw = (
            data["building_file"] if "building_file" in data else data["building_path"]
        )
        weather_raw = (
            data["weather_file"] if "weather_file" in data else data["weather_path"]
        )

        building_path = (
            str((repo_root / building_raw).resolve())
            if not Path(building_raw).is_absolute()
            else str(Path(building_raw))
        )
        weather_path = (
            str((repo_root / weather_raw).resolve())
            if not Path(weather_raw).is_absolute()
            else str(Path(weather_raw))
        )
        resolved_output_path = (
            str((repo_root / output_path_raw).resolve())
            if not Path(output_path_raw).is_absolute()
            else str(Path(output_path_raw))
        )

        config = cls(
            building_path=building_path,
            weather_path=weather_path,
            output_path=resolved_output_path,
            env_name=env_name,
            mode=mode,
            variables=variables,
            meters=meters,
            actuators=actuators,
            time_variables=list(
                observation_config.get("time_variables", data.get("time_variables", []))
            ),
            output_csv=bool(output_config.get("csv", True)),
            output_log=bool(output_config.get("log", True)),
            max_keep_files=int(output_config.get("max_keep_files", 10)),
            step_timeout_seconds=float(data.get("step_timeout_seconds", 60.0)),
            queue_put_timeout_seconds=float(data.get("queue_put_timeout_seconds", 5.0)),
            shutdown_timeout_seconds=float(data.get("shutdown_timeout_seconds", 15.0)),
            drl=drl_config if isinstance(drl_config, dict) else {},
            runperiod_start=runperiod_config.get("start", data.get("runperiod_start")),
            runperiod_end=runperiod_config.get("end", data.get("runperiod_end")),
            timesteps_per_hour=int(data.get("timesteps_per_hour", 1)),
        )
        config.validate()
        return config

    @classmethod
    def from_file(cls, config_path: str) -> "SimulationConfig":
        """Load JSON/YAML config and parse into a validated SimulationConfig."""
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {config_path}")
        with path.open("r", encoding="utf-8") as fp:
            if path.suffix.lower() == ".json":
                data = json.load(fp)
            elif path.suffix.lower() in {".yaml", ".yml"}:
                try:
                    import yaml
                except ImportError as exc:
                    raise ImportError(
                        "PyYAML is required for YAML config files"
                    ) from exc
                data = yaml.safe_load(fp)
            else:
                raise ValueError(
                    "Only .json, .yaml and .yml config files are supported"
                )
        if not isinstance(data, dict):
            raise ValueError("Config content must be a mapping object")
        # Convert the raw config dict into a SimulationConfig instance and validate it
        return cls.from_dict(data)

    @staticmethod
    def _normalize_drl_config(raw: Any) -> Dict[str, Any]:
        """Merge user-provided DRL settings with default values."""
        source = raw if isinstance(raw, dict) else {}
        drl = dict(source)
        # If the user does not provide a config section, set it to an empty dict
        drl.setdefault("reward_weights", {})
        drl.setdefault("algo_params", {})
        drl.setdefault("env_wrapper_params", {})
        drl.setdefault("runtime_params", {})

        # Ensure each subsection is a dict
        if not isinstance(drl["reward_weights"], dict):
            drl["reward_weights"] = {}
        if not isinstance(drl["algo_params"], dict):
            drl["algo_params"] = {}
        if not isinstance(drl["env_wrapper_params"], dict):
            drl["env_wrapper_params"] = {}
        if not isinstance(drl["runtime_params"], dict):
            drl["runtime_params"] = {}
        # Safe defaults for every parameter
        defaults = {
            "reward_weights": {
                "energy": 1e-6,
                "comfort": 0.1,
                "action_l2": 0.01,
                "bias": 0.0,
            },
            "algo_params": {
                "batch_size": 32,
                "buffer_size": 5000,
                "learning_rate": 3e-4,
                "gamma": 0.99,
                "tau": 0.01,
                "ppo_rollout_steps": 32,
                "policy_delay": 2,
                "policy_noise": 0.02,
            },
            "env_wrapper_params": {
                "normalize_action": bool(drl.get("normalize_action", False)),
                "normalize_observation": bool(drl.get("normalize_observation", False)),
                "normalize_reward": bool(drl.get("normalize_reward", False)),
                "obs_norm_clip": 10.0,
                "obs_norm_epsilon": 1e-8,
                "reward_scale": 1.0,
                "reward_norm_gamma": 0.99,
                "reward_norm_epsilon": 1e-8,
            },
            "runtime_params": {
                "train_episodes": int(drl.get("train_episodes", 10)),
                "seed": int(drl.get("seed", 0)),
                "evaluate_every": int(drl.get("evaluate_every", 0)),
                "eval_episodes": int(drl.get("eval_episodes", 1)),
            },
        }
        # Merge: user value takes precedence, otherwise use default
        for section, section_defaults in defaults.items():
            target = drl[section]
            for key, value in section_defaults.items():
                target.setdefault(key, value)
        return drl

    def _validate_drl(self) -> None:
        """Validate DRL-specific invariants and guard against invalid ranges."""
        drl = self.drl if isinstance(self.drl, dict) else {}

        # Validate action space type and bounds
        action_space_type = str(drl.get("action_space_type", "box")).lower()
        if action_space_type not in {"box", "discrete"}:
            raise ValueError("drl.action_space_type must be box or discrete")
        has_action_bounds = isinstance(drl.get("action_low"), list) or isinstance(
            drl.get("action_high"), list
        )
        if action_space_type == "discrete" and has_action_bounds:
            raise ValueError(
                "discrete action space must not define action_low/action_high"
            )

        # Validate environment wrapper parameters
        env_wrapper = drl.get("env_wrapper_params", {})
        if isinstance(env_wrapper, dict):
            # Validate normalize_action parameter
            normalize_action = bool(env_wrapper.get("normalize_action", False))
            if normalize_action and action_space_type != "box":
                raise ValueError("normalize_action requires box action space")

            # Validate obs_norm_clip parameter
            obs_norm_clip = float(env_wrapper.get("obs_norm_clip", 10.0))
            if obs_norm_clip <= 0:
                raise ValueError("drl.env_wrapper_params.obs_norm_clip must be > 0")

            # Validate reward_norm_gamma parameter
            reward_norm_gamma = float(env_wrapper.get("reward_norm_gamma", 0.99))
            if reward_norm_gamma <= 0 or reward_norm_gamma > 1:
                raise ValueError(
                    "drl.env_wrapper_params.reward_norm_gamma must be in (0,1]"
                )

        runtime_params = drl.get("runtime_params", {})
        if isinstance(runtime_params, dict):
            for key in ["train_episodes", "evaluate_every", "eval_episodes"]:
                value = int(runtime_params.get(key, 0))
                if value < 0:
                    raise ValueError(f"drl.runtime_params.{key} must be >= 0")

    @property
    def env_id(self) -> str:
        """Return the Gym registration id derived from env_name and suffix."""
        suffix = self.drl.get("env_suffix", "v1")
        # Example Eplus-{Building1-rule}-v1, Eplus-{Building2-drl}-v1
        return f"Eplus-{self.env_name}-{suffix}"

    @staticmethod
    def _parse_variables(raw: Any) -> Dict[str, Tuple[str, str]]:
        """
        Normalize variable definitions to ``{alias: (variable_name, key_value)}``.

        Supports tuple/list pair or dict payloads with keys such as
        ``variable_name`` and ``key_value``.
        """
        if not raw:
            return {}
        parsed: Dict[str, Tuple[str, str]] = {}
        # Example: {'Zone Mean Air Temperature': ('Zone Mean Air Temperature', '*')}
        for key, value in raw.items():
            if isinstance(value, (list, tuple)) and len(value) == 2:
                parsed[key] = (str(value[0]), str(value[1]))
            elif isinstance(value, dict):
                variable_name = value.get("variable_name") or value.get("name") or key
                key_value = (
                    value.get("key_value")
                    or value.get("key")
                    or value.get("keys")
                    or "*"
                )
                parsed[key] = (str(variable_name), str(key_value))
            else:
                raise ValueError(f"Invalid variable definition for {key}")
        return parsed

    @staticmethod
    def _parse_meters(raw: Any) -> Dict[str, str]:
        """Normalize meter definitions to ``{alias: meter_name}``."""
        if not raw:
            return {}
        parsed: Dict[str, str] = {}
        for key, value in raw.items():
            parsed[key] = str(value)
        return parsed

    @staticmethod
    def _parse_actuators(raw: Any) -> Dict[str, Tuple[str, str, str]]:
        """
        Normalize actuator definitions to ``{alias: (component, control, key)}``.

        Accepts tuple/list triplets or dict payloads containing component type,
        control type, and actuator key.
        """
        if not raw:
            return {}
        parsed: Dict[str, Tuple[str, str, str]] = {}
        for key, value in raw.items():
            if isinstance(value, (list, tuple)) and len(value) == 3:
                parsed[key] = (str(value[0]), str(value[1]), str(value[2]))
                continue
            if isinstance(value, dict):
                component_type = value.get("component_type") or value.get(
                    "element_type"
                )
                control_type = value.get("control_type") or value.get("value_type")
                actuator_key = value.get("actuator_key") or value.get("name") or key
                if not component_type or not control_type:
                    raise ValueError(f"Invalid actuator definition for {key}")
                parsed[key] = (
                    str(component_type),
                    str(control_type),
                    str(actuator_key),
                )
                continue
            raise ValueError(f"Invalid actuator definition for {key}")
        return parsed


class IDFManager:
    """
    Prepare a runnable IDF by applying config-driven outputs and schedules.

    Responsibilities:
    - Resolve IDD path (via EPLUS_PATH or default install path).
    - Load the base IDF with eppy.
    - Inject Output:Variable and Output:Meter objects.
    - Apply timestep and run period overrides.

    Example:
        >>> manager = IDFManager(config)  # doctest: +SKIP
        >>> idf_path = manager.prepare_simulation()
    """

    def __init__(self, config: SimulationConfig):
        self.logger = Logger().getLogger("IDF_MANAGER", LOG_MODEL_LEVEL)
        self.config = config

        eplus_path = os.environ.get("EPLUS_PATH")
        # Check if EPLUS_PATH is set, otherwise use default
        if not eplus_path:
            eplus_path = "/usr/local/EnergyPlus-23-1-0"
            if not os.path.exists(eplus_path):
                self.logger.warning(
                    f"EPLUS_PATH not set and default {eplus_path} not found."
                )

        # EnergyPlus requires the IDD (Input Data Dictionary) to understand the structure of .idf files
        idd_path = os.path.join(eplus_path, "Energy+.idd")
        if not os.path.exists(idd_path):
            self.logger.error(
                f"IDD file not found at {idd_path}. Please set EPLUS_PATH correctly."
            )
        try:
            IDF.setiddname(idd_path)
        except Exception as e:
            self.logger.warning(
                f"Failed to set IDD name: {e}. If IDD is already set, this is fine."
            )

        # Load the base IDF file using eppy
        self.idf = IDF(self.config.building_path)
        self.logger.info(f"Loaded IDF file: {self.config.building_path}")

    def prepare_simulation(self) -> str:
        """Apply config overrides and save the modified IDF into output_path."""
        self._apply_timestep()  # Update or create TIMESTEP object
        self._apply_runperiod()  # Update or create RUNPERIOD object
        self._apply_sqlite_output()  # Ensure eplusout.sql is generated.
        # append Output:Variable objects to the IDF
        for variable_name, key_value in self.config.variables.values():
            self.idf.newidfobject(
                "Output:Variable",
                Key_Value=key_value,
                Variable_Name=variable_name,
                Reporting_Frequency="Timestep",
            )
            self.logger.debug(f"Added Output:Variable {variable_name} ({key_value})")
        # append Output:Meter objects to the IDF
        for meter_name in self.config.meters.values():
            self.idf.newidfobject(
                "Output:Meter", Key_Name=meter_name, Reporting_Frequency="Timestep"
            )
            self.logger.debug(f"Added Output:Meter {meter_name}")

        os.makedirs(self.config.output_path, exist_ok=True)
        output_idf_path = os.path.join(self.config.output_path, "in.idf")
        self.idf.saveas(output_idf_path)
        self.logger.info(f"Saved modified IDF to: {output_idf_path}")
        return output_idf_path

    def _apply_sqlite_output(self) -> None:
        """Ensure EnergyPlus writes eplusout.sql for downstream exports."""
        sqlite_objects = self.idf.idfobjects.get("OUTPUT:SQLITE", [])
        if sqlite_objects:
            sqlite_objects[0].Option_Type = "SimpleAndTabular"
            return
        self.idf.newidfobject("Output:SQLite", Option_Type="SimpleAndTabular")

    def _apply_timestep(self) -> None:
        """Ensure the IDF has a TIMESTEP object matching config."""
        timestep_objects = self.idf.idfobjects.get("TIMESTEP", [])
        # Update existing TIMESTEP object or create a new one if none exists
        if timestep_objects:
            timestep_objects[
                0
            ].Number_of_Timesteps_per_Hour = self.config.timesteps_per_hour
        else:
            self.idf.newidfobject(
                "Timestep", Number_of_Timesteps_per_Hour=self.config.timesteps_per_hour
            )

    def _apply_runperiod(self) -> None:
        """Override RunPeriod bounds when start/end dates are provided."""
        # Check if run period dates are specified in config
        if not self.config.runperiod_start or not self.config.runperiod_end:
            # If not specified, use default RunPeriod
            return
        start_date = date.fromisoformat(self.config.runperiod_start)
        end_date = date.fromisoformat(self.config.runperiod_end)
        runperiod_objects = self.idf.idfobjects.get("RUNPERIOD", [])

        # Update the first RUNPERIOD object and remove any others to avoid multi-period simulation
        if runperiod_objects:
            runperiod = runperiod_objects[0]
            # Remove other RunPeriod objects if any
            for i in range(len(runperiod_objects) - 1, 0, -1):
                self.idf.removeidfobject(runperiod_objects[i])
        else:
            runperiod = self.idf.newidfobject("RunPeriod")

        # Set the run period start and end dates
        runperiod.Begin_Month = start_date.month
        runperiod.Begin_Day_of_Month = start_date.day
        runperiod.End_Month = end_date.month
        runperiod.End_Day_of_Month = end_date.day
