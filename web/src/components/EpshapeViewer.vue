<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, shallowRef } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { Line2 } from 'three/examples/jsm/lines/Line2.js';
import { LineMaterial } from 'three/examples/jsm/lines/LineMaterial.js';
import { LineGeometry } from 'three/examples/jsm/lines/LineGeometry.js';
import { useI18n } from 'vue-i18n';
import { triangulatedSurfacefromVertlist } from '../utils/geometry';
import { useTheme } from '../composables/useTheme';

const props = withDefaults(defineProps<{
  geometryData: any;
  isMaximized: boolean;
  showFullscreenButton?: boolean;
}>(), {
  showFullscreenButton: true,
});

const emit = defineEmits<{
  (e: 'toggle-maximize'): void;
}>();

const { isDark, theme } = useTheme();
const { t } = useI18n();

const viewerRoot = ref<HTMLElement | null>(null);
const canvasHost = ref<HTMLElement | null>(null);
const tooltip = ref<HTMLElement | null>(null);
const tooltipData = ref<any>(null);

// Three.js instances
// Use shallowRef for Three.js objects to avoid Vue reactivity overhead
const sceneRef = shallowRef<THREE.Scene | null>(null);
const cameraRef = shallowRef<THREE.PerspectiveCamera | null>(null);
const rendererRef = shallowRef<THREE.WebGLRenderer | null>(null);
const controlsRef = shallowRef<OrbitControls | null>(null);
const dirLightRef = shallowRef<THREE.DirectionalLight | null>(null);
const ambientLightRef = shallowRef<THREE.AmbientLight | null>(null);

const raycaster = new THREE.Raycaster();
const mouse = new THREE.Vector2();

let animationId: number;
let bldgCenter: number[] = [0, 0, 0];
let bldgRadius: number = 100;
let isDraggingCamera = false;
let lastHoverSampleAt = 0;

const HOVER_SAMPLE_INTERVAL_MS = 80;
const MIN_CAMERA_FAR = 1000;
const CAMERA_FIT_PADDING = 1.22;
const CAMERA_FAR_PADDING_MULTIPLIER = 6;
const CAMERA_MAX_DISTANCE_MULTIPLIER = 3.2;
const NAVIGATION_SENSITIVITY_MIN = 0.6;
const NAVIGATION_SENSITIVITY_MAX = 1.8;
const ORBIT_REFERENCE_VIEWPORT_DIAGONAL = 1100;
const ORBIT_BASE_ROTATE_SPEED = 0.88;
const ORBIT_BASE_ZOOM_SPEED = 1.35;
const ORBIT_BASE_PAN_SPEED = 1.18;
const ORBIT_BASE_DAMPING = 0.07;
const cameraFitDirection = new THREE.Vector3(1, -1, 0.75).normalize();

const showSettingsPanel = ref(false);
const showVisibilityPanel = ref(false);
const showHelpPanel = ref(false);

type ViewerPanel = 'settings' | 'visibility' | 'help';

const panelWidths: Record<ViewerPanel, number> = {
  settings: 350,
  visibility: 350,
  help: 500,
};
const panelPositions = ref<Record<ViewerPanel, { x: number; y: number }>>({
  settings: { x: 16, y: 56 },
  visibility: { x: 16, y: 56 },
  help: { x: 16, y: 56 },
});
let activePanelDrag:
  | {
      panel: ViewerPanel;
      startX: number;
      startY: number;
      originX: number;
      originY: number;
    }
  | null = null;

const settings = ref({
  showZones: true,
  showShading: true,
  showEdges: true,
  ghostMode: false, // For hidden objects
  colorMode: 'surfaceType' as 'surfaceType' | 'construction',
  opacity: 0.6, // Window opacity
  shadows: true,
  wireframe: false,
  hiddenObjectMode: 'disable' as 'disable' | 'wireframe' | 'ghost',
  heightMin: -1e9,
  heightMax: 1e9,
  shadowAlt: 45,
  shadowAzm: 90,
  shadowMapSize: 1024,
  shadowRadius: 1,
  shadowHeight: 0,
  selfShadow: false,
  showAxes: false,
  showNorth: false,
  cameraFar: 1000,
  maxZoom: 950,
  cameraFov: 30,
  navigationSensitivity: 1,
  edgeThickness: 2,
  transparencyOn: true,
  shadingOn: true,
  edgeThicknessOn: true,
  debugOn: false,
});

const visFilterType = ref<'zones' | 'height' | 'both'>('zones');

const axesHelperRef = shallowRef<THREE.AxesHelper | null>(null);
const northArrowRef = shallowRef<THREE.Line | null>(null);
const shadowCatcherRef = shallowRef<THREE.Mesh | null>(null);

const zoneVisibility = ref<Record<string, boolean>>({});
const bounds = ref({ minZ: 0, maxZ: 100 });
const constructionColors = ref<Record<string, number>>({});

const hoveredObject = ref<any>(null);

// Colors
const colors = ref({
  wall: 0xcccccc,
  roof: 0xaa5555,
  floor: 0x555555,
  window: 0x88ccff,
  shade: 0x888888,
  edge: 0x000000,
  selection: 0xff0000,
});

const isRotating = ref(false);
const isSlicing = ref(false);

const showCommandPrompt = ref(false);
const commandInput = ref('');
const commandInputRef = ref<HTMLInputElement | null>(null);

const clamp = (num: number, min: number, max: number) => Math.min(Math.max(num, min), max);

function getViewportDiagonal() {
  const host = canvasHost.value;
  return Math.max(1, Math.hypot(host?.clientWidth ?? 1, host?.clientHeight ?? 1));
}

function getOrbitInteractionProfile() {
  const sensitivity = clamp(
    settings.value.navigationSensitivity,
    NAVIGATION_SENSITIVITY_MIN,
    NAVIGATION_SENSITIVITY_MAX,
  );
  const viewportScale = clamp(
    Math.sqrt(getViewportDiagonal() / ORBIT_REFERENCE_VIEWPORT_DIAGONAL),
    0.82,
    1.24,
  );

  return {
    rotateSpeed: ORBIT_BASE_ROTATE_SPEED * sensitivity * viewportScale,
    zoomSpeed: ORBIT_BASE_ZOOM_SPEED * sensitivity,
    panSpeed: ORBIT_BASE_PAN_SPEED * sensitivity * viewportScale,
    dampingFactor: clamp(ORBIT_BASE_DAMPING / Math.sqrt(sensitivity), 0.045, 0.11),
    keyPanSpeed: Math.round(clamp((getViewportDiagonal() / 28) * sensitivity, 16, 72)),
  };
}

function applyOrbitInteractionProfile(controls = controlsRef.value) {
  if (!controls) return;
  const profile = getOrbitInteractionProfile();
  controls.enableDamping = true;
  controls.dampingFactor = profile.dampingFactor;
  controls.rotateSpeed = profile.rotateSpeed;
  controls.zoomSpeed = profile.zoomSpeed;
  controls.panSpeed = profile.panSpeed;
  controls.keyPanSpeed = profile.keyPanSpeed;
  controls.screenSpacePanning = true;
  controls.zoomToCursor = true;
  controls.mouseButtons = {
    LEFT: THREE.MOUSE.ROTATE,
    MIDDLE: THREE.MOUSE.DOLLY,
    RIGHT: THREE.MOUSE.PAN,
  };
  controls.touches = {
    ONE: THREE.TOUCH.ROTATE,
    TWO: THREE.TOUCH.DOLLY_PAN,
  };
  controls.maxDistance = settings.value.maxZoom;
}

const clampPanelPosition = (panel: ViewerPanel, x: number, y: number) => {
  const root = viewerRoot.value;
  const width = panelWidths[panel];
  const maxX = Math.max(16, (root?.clientWidth ?? width + 32) - width - 16);
  const maxY = Math.max(56, (root?.clientHeight ?? 600) - 120);
  return {
    x: clamp(x, 16, maxX),
    y: clamp(y, 56, maxY),
  };
};

const panelStyle = (panel: ViewerPanel) => {
  const pos = panelPositions.value[panel];
  return {
    left: `${pos.x}px`,
    top: `${pos.y}px`,
  };
};

const ensurePanelPosition = (panel: ViewerPanel) => {
  const root = viewerRoot.value;
  if (!root) return;
  const width = panelWidths[panel];
  const current = panelPositions.value[panel];
  if (current.x === 16 && current.y === 56) {
    panelPositions.value[panel] = clampPanelPosition(
      panel,
      root.clientWidth - width - 16,
      56,
    );
  }
};

const onPanelPointerMove = (event: PointerEvent) => {
  if (!activePanelDrag) return;
  const { panel, startX, startY, originX, originY } = activePanelDrag;
  panelPositions.value[panel] = clampPanelPosition(
    panel,
    originX + event.clientX - startX,
    originY + event.clientY - startY,
  );
};

const stopPanelDrag = () => {
  activePanelDrag = null;
  window.removeEventListener('pointermove', onPanelPointerMove);
  window.removeEventListener('pointerup', stopPanelDrag);
};

const startPanelDrag = (panel: ViewerPanel, event: PointerEvent) => {
  event.preventDefault();
  const pos = panelPositions.value[panel];
  activePanelDrag = {
    panel,
    startX: event.clientX,
    startY: event.clientY,
    originX: pos.x,
    originY: pos.y,
  };
  window.addEventListener('pointermove', onPanelPointerMove);
  window.addEventListener('pointerup', stopPanelDrag);
};

const closeAllPanels = () => {
  showSettingsPanel.value = false;
  showVisibilityPanel.value = false;
  showHelpPanel.value = false;
};

const togglePanel = (panel: 'settings' | 'visibility' | 'help') => {
  const next = panel === 'settings'
    ? !showSettingsPanel.value
    : panel === 'visibility'
      ? !showVisibilityPanel.value
      : !showHelpPanel.value;

  closeAllPanels();

  if (next) ensurePanelPosition(panel);
  if (panel === 'settings') showSettingsPanel.value = next;
  if (panel === 'visibility') showVisibilityPanel.value = next;
  if (panel === 'help') showHelpPanel.value = next;
};

const changeVisFilter = (t: 'zones' | 'height' | 'both') => {
  visFilterType.value = t;
  updateVisibility();
};

const changeZoneAll = (visible: boolean) => {
  Object.keys(zoneVisibility.value).forEach((z) => {
    zoneVisibility.value[z] = visible;
  });
};

const resetHeightRange = () => {
  settings.value.heightMin = bounds.value.minZ;
  settings.value.heightMax = bounds.value.maxZ;
};

const updateHeightMin = (v: number) => {
  const next = clamp(v, bounds.value.minZ, settings.value.heightMax);
  settings.value.heightMin = next;
};

const updateHeightMax = (v: number) => {
  const next = clamp(v, settings.value.heightMin, bounds.value.maxZ);
  settings.value.heightMax = next;
};

const exportImage = () => {
  takeScreenshot();
};

const executeCommand = () => {
  const cmd = commandInput.value.trim().toLowerCase();
  commandInput.value = '';
  showCommandPrompt.value = false;
  
  if (!cmd) return;
  
  const parts = cmd.split(' ');
  const baseCmd = parts[0];
  const arg = parts.length > 1 ? parts[1] : null;

  switch (baseCmd) {
    case 'help':
      showHelpPanel.value = true;
      break;
    case 'shadowalt':
      if (arg && !isNaN(parseFloat(arg))) {
        settings.value.shadowAlt = parseFloat(arg);
        updateLights();
      }
      break;
    case 'shadowazm':
      if (arg && !isNaN(parseFloat(arg))) {
        settings.value.shadowAzm = parseFloat(arg);
        updateLights();
      }
      break;
    case 'shadowmapsize':
      if (arg && !isNaN(parseInt(arg))) {
        settings.value.shadowMapSize = parseInt(arg);
        if (dirLightRef.value) {
          dirLightRef.value.shadow.mapSize.width = settings.value.shadowMapSize;
          dirLightRef.value.shadow.mapSize.height = settings.value.shadowMapSize;
          dirLightRef.value.shadow.map?.dispose();
          dirLightRef.value.shadow.map = null as any;
        }
      }
      break;
    case 'shadowradius':
      if (arg && !isNaN(parseFloat(arg))) {
        settings.value.shadowRadius = parseFloat(arg);
      }
      break;
    case 'shadowheight':
      if (arg && !isNaN(parseFloat(arg))) {
        settings.value.shadowHeight = parseFloat(arg);
      }
      break;
    case 'selfshadow':
      if (arg === 'on') settings.value.selfShadow = true;
      else if (arg === 'off') settings.value.selfShadow = false;
      break;
    case 'camerafar':
      if (arg && !isNaN(parseFloat(arg))) {
        settings.value.cameraFar = parseFloat(arg);
        if (cameraRef.value) {
          cameraRef.value.far = settings.value.cameraFar;
          cameraRef.value.updateProjectionMatrix();
        }
      }
      break;
    case 'maxzoom':
      if (arg && !isNaN(parseFloat(arg))) {
        settings.value.maxZoom = parseFloat(arg);
        applyOrbitInteractionProfile();
      }
      break;
    case 'camerafov':
      if (arg && !isNaN(parseFloat(arg))) {
        settings.value.cameraFov = parseFloat(arg);
        if (cameraRef.value) {
          cameraRef.value.fov = settings.value.cameraFov;
          cameraRef.value.updateProjectionMatrix();
        }
      }
      break;
    case 'animatecamera': {
      const arg2 = parts.length > 2 ? parts[2] : null;
      const frames = arg && !isNaN(parseInt(arg)) ? parseInt(arg) : 36;
      const dir = arg2 === 'ccw' ? 'ccw' : 'cw';
      exportCameraAnimFrames(frames, dir);
      break;
    }
    case 'animateheight': {
      const arg2 = parts.length > 2 ? parts[2] : null;
      const frames = arg && !isNaN(parseInt(arg)) ? parseInt(arg) : 36;
      const dir = arg2 === 'dn' ? 'dn' : 'up';
      exportSliceAnimFrames(frames, dir);
      break;
    }
    // Add other commands as needed
  }
};

const exportCameraAnimFrames = async (frames: number, dir: 'cw' | 'ccw') => {
  if (!rendererRef.value || !sceneRef.value || !cameraRef.value || !controlsRef.value) return;
  const originalAngle = controlsRef.value.getAzimuthalAngle();
  const distance = cameraRef.value.position.distanceTo(controlsRef.value.target);
  const polarAngle = controlsRef.value.getPolarAngle();

  for (let i = 0; i < frames; i++) {
    const step = (i * Math.PI * 2) / frames;
    const angle = originalAngle + (dir === 'cw' ? step : -step);
    const target = controlsRef.value.target;
    const radiusXY = distance * Math.sin(polarAngle);
    cameraRef.value.position.x = target.x + radiusXY * Math.sin(angle);
    cameraRef.value.position.y = target.y + radiusXY * Math.cos(angle);
    cameraRef.value.position.z = target.z + distance * Math.cos(polarAngle);

    controlsRef.value.update();
    rendererRef.value.render(sceneRef.value, cameraRef.value);

    const dataURL = rendererRef.value.domElement.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = `anim-cam-${i.toString().padStart(3, '0')}.png`;
    link.href = dataURL;
    link.click();

    await new Promise(r => setTimeout(r, 25));
  }
};

const exportSliceAnimFrames = async (frames: number, dir: 'up' | 'dn') => {
  if (!rendererRef.value || !sceneRef.value || !cameraRef.value) return;
  const originalMin = settings.value.heightMin;
  const originalMax = settings.value.heightMax;
  const minZ = bounds.value.minZ;
  const maxZ = bounds.value.maxZ;
  const range = maxZ - minZ;

  for (let i = 0; i < frames; i++) {
    const t = frames <= 1 ? 0 : i / (frames - 1);
    const z = dir === 'up' ? (minZ + range * t) : (maxZ - range * t);
    settings.value.heightMin = minZ;
    settings.value.heightMax = z;
    updateVisibility();
    rendererRef.value.render(sceneRef.value, cameraRef.value);

    const dataURL = rendererRef.value.domElement.toDataURL('image/png');
    const link = document.createElement('a');
    link.download = `anim-slice-${i.toString().padStart(3, '0')}.png`;
    link.href = dataURL;
    link.click();

    await new Promise(r => setTimeout(r, 25));
  }

  settings.value.heightMin = originalMin;
  settings.value.heightMax = originalMax;
  updateVisibility();
};

const toggleRotation = () => {
  isRotating.value = !isRotating.value;
  if (controlsRef.value) {
    controlsRef.value.autoRotate = isRotating.value;
  }
};

const toggleSlice = () => {
  isSlicing.value = !isSlicing.value;
  if (!isSlicing.value) {
    resetHeightRange();
  } else {
    settings.value.heightMin = bounds.value.minZ;
    settings.value.heightMax = bounds.value.minZ;
  }
};

const cameraDir = new THREE.Vector3();

const updateLights = () => {
  if (!dirLightRef.value || !cameraRef.value) return;
  const alt = (settings.value.shadowAlt * Math.PI) / 180;
  
  // Calculate displayAzm based on camera position like EPShape
  cameraRef.value.getWorldDirection(cameraDir);
  const displayAzm = Math.atan2(cameraDir.x, cameraDir.y);
  
  const azm = displayAzm + (settings.value.shadowAzm * Math.PI) / 180;
  
  const r = bldgRadius * 2;
  const x = bldgCenter[0] + r * Math.cos(alt) * Math.sin(azm);
  const y = bldgCenter[1] + r * Math.cos(alt) * Math.cos(azm);
  const z = bldgCenter[2] + r * Math.sin(alt);
  
  dirLightRef.value.position.set(x, y, z);
  dirLightRef.value.target.position.set(bldgCenter[0], bldgCenter[1], bldgCenter[2]);
  dirLightRef.value.target.updateMatrixWorld();
};

function getLineMaterialResolution() {
  const host = canvasHost.value;
  const canvas = rendererRef.value?.domElement;
  return {
    width: host?.clientWidth || canvas?.clientWidth || canvas?.width || window.innerWidth,
    height: host?.clientHeight || canvas?.clientHeight || canvas?.height || window.innerHeight,
  };
}

function applyEdgeMaterialSettings(line: any) {
  const material = line.material as LineMaterial;
  const resolution = getLineMaterialResolution();
  line.visible = settings.value.showEdges;
  material.linewidth = settings.value.edgeThicknessOn ? settings.value.edgeThickness : 1;
  material.resolution.set(resolution.width, resolution.height);
  material.needsUpdate = true;
}

function applyShadowSettings() {
  if (sceneRef.value) {
    sceneRef.value.traverse((child) => {
      if ((child as any).isMesh) {
        const mesh = child as THREE.Mesh;
        if (!mesh.userData?.type) return;
        mesh.castShadow = settings.value.shadows;
        mesh.receiveShadow = settings.value.shadows && settings.value.selfShadow;
      }
    });
  }

  if (shadowCatcherRef.value) {
    shadowCatcherRef.value.visible = settings.value.shadows;
    shadowCatcherRef.value.position.setZ(settings.value.shadowHeight);
  }

  if (dirLightRef.value) {
    dirLightRef.value.castShadow = settings.value.shadows;
    dirLightRef.value.shadow.radius = settings.value.shadowRadius;
  }

  updateLights();
}

const setupLights = (scene: THREE.Scene) => {
  const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
  scene.add(ambientLight);
  ambientLightRef.value = ambientLight;

  const dirLight = new THREE.DirectionalLight(0xffffff, 0.8);
  dirLight.castShadow = true;
  dirLight.shadow.camera.top = 500;
  dirLight.shadow.camera.bottom = -500;
  dirLight.shadow.camera.left = -500;
  dirLight.shadow.camera.right = 500;
  dirLight.shadow.camera.near = 0.1;
  dirLight.shadow.camera.far = 2000;
  dirLight.shadow.mapSize.width = 1024;
  dirLight.shadow.mapSize.height = 1024;
  scene.add(dirLight);
  scene.add(dirLight.target);
  
  dirLightRef.value = dirLight;
  updateThemeLighting();
  updateLights();
};

const themeColor = (name: string, fallback: string) => {
  if (typeof window === 'undefined') return fallback;
  const value = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return value || fallback;
};

const updateBackground = () => {
  const scene = sceneRef.value;
  const renderer = rendererRef.value;
  if (!scene) return;

  const color = new THREE.Color(themeColor('--app-panel-2', isDark.value ? '#111827' : '#ffffff'));
  scene.background = color;
  if (renderer) {
    renderer.setClearColor(color, 1);
  }
};

const updateThemeLighting = () => {
  if (ambientLightRef.value) {
    ambientLightRef.value.intensity = isDark.value ? 0.55 : 0.42;
  }
  if (dirLightRef.value) {
    dirLightRef.value.intensity = isDark.value ? 1.05 : 0.9;
  }
  if (shadowCatcherRef.value) {
    const material = shadowCatcherRef.value.material as THREE.ShadowMaterial;
    material.opacity = isDark.value ? 0.32 : 0.42;
    material.needsUpdate = true;
  }
};

const initScene = () => {
  if (!canvasHost.value) return;
  
  const scene = new THREE.Scene();
  sceneRef.value = scene;
  updateBackground();

  const width = canvasHost.value.clientWidth;
  const height = canvasHost.value.clientHeight;

  const camera = new THREE.PerspectiveCamera(settings.value.cameraFov, width / height, 0.1, settings.value.cameraFar);
  cameraRef.value = camera;
  
  const renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: false });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 1.75));
  renderer.setSize(width, height);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  rendererRef.value = renderer;
  
  while (canvasHost.value.firstChild) {
    canvasHost.value.removeChild(canvasHost.value.firstChild);
  }
  canvasHost.value.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  applyOrbitInteractionProfile(controls);
  controls.listenToKeyEvents(window); // Allow keyboard controls if needed
  controls.addEventListener('start', () => {
    isDraggingCamera = true;
    hoveredObject.value = null;
    tooltipData.value = null;
  });
  controls.addEventListener('end', () => {
    isDraggingCamera = false;
    if (isShiftDown.value) {
      snapCamera();
    }
  });
  
  controlsRef.value = controls;

  // Lights
  setupLights(scene);

  // Initial Render
  createGeometry();

  // Animation Loop
  const animate = () => {
    animationId = requestAnimationFrame(animate);
    const controlsChanged = controls.update();
    
    // update lights if camera moves, since shadow azimuth is relative to camera
    if (controlsChanged || isRotating.value) updateLights();
    
    if (isSlicing.value) {
       let step = (bounds.value.maxZ - bounds.value.minZ) * 0.01;
       if (step < 0.1) step = 0.1;

       settings.value.heightMin = bounds.value.minZ;
       settings.value.heightMax += step;
       if (settings.value.heightMax > bounds.value.maxZ) {
         settings.value.heightMax = bounds.value.minZ;
       }
    }
    
    renderer.render(scene, camera);
  };
  animate();

  // Event Listeners
  window.addEventListener('resize', handleResize);
  window.addEventListener('keydown', handleKeydown);
  window.addEventListener('keyup', handleKeyup);
  canvasHost.value.addEventListener('mousemove', onMouseMove);
  canvasHost.value.addEventListener('click', onMouseClick);
};

const updateVisibility = () => {
  if (!sceneRef.value) return;
  
  sceneRef.value.traverse((child) => {
    if ((child as any).isMesh) {
      const mesh = child as THREE.Mesh;
      const data = mesh.userData;
      
      if (!data || !data.type) return;

      let isHidden = false;

      // Filter by Zone Visibility
      if (visFilterType.value === 'zones' || visFilterType.value === 'both') {
        if (data.ZoneName && zoneVisibility.value[data.ZoneName] === false) {
          isHidden = true;
        }
        else if (data.type === 'Fenestration' && data.BuildingSurfaceName) {
          if (data.ZoneName && zoneVisibility.value[data.ZoneName] === false) {
            isHidden = true;
          }
        }
      }

      // Filter by Type
      if (data.type === 'BuildingSurface' && !settings.value.showZones) isHidden = true;
      if (data.type === 'Shading' && !settings.value.showShading) isHidden = true;
      if (data.type === 'BuildingSurface' && !settings.value.shadingOn && data.SurfaceType?.toLowerCase() === 'shading') isHidden = true;
      
      // Filter by Height
      if (!isHidden && data.centerZ !== undefined && (visFilterType.value === 'height' || visFilterType.value === 'both')) {
        if (data.centerZ < settings.value.heightMin || data.centerZ > settings.value.heightMax) isHidden = true;
      }

      const mat = mesh.material as THREE.MeshPhongMaterial;
      
      // Dynamic update of materials based on colors.value
      // Note: Since we cloned materials, we need to update them if colors change
      // But creating new geometry every time is expensive.
      // Better to traverse and update material colors if mode is SurfaceType
      
      if (data.type === 'BuildingSurface') {
         if (settings.value.colorMode === 'construction' && data.Construction) {
             const colorHex = getConstructionColor(data.Construction);
             mat.color.setHex(colorHex);
         } else {
             // Reset to original color based on type
             if (data.SurfaceType?.toUpperCase() === 'ROOF') mat.color.setHex(colors.value.roof);
             else if (data.SurfaceType?.toUpperCase() === 'FLOOR') mat.color.setHex(colors.value.floor);
             else mat.color.setHex(colors.value.wall);
         }
      } else if (data.type === 'Fenestration') {
         mat.color.setHex(colors.value.window);
      } else if (data.type === 'Shading') {
         mat.color.setHex(colors.value.shade);
      }

      if (data.type === 'BuildingSurface' && !settings.value.transparencyOn) {
        mat.transparent = false;
        mat.opacity = 1;
      }

      if (isHidden) {
          if (settings.value.hiddenObjectMode === 'disable') {
              mesh.visible = false;
          } else if (settings.value.hiddenObjectMode === 'wireframe') {
              mesh.visible = true;
              mat.wireframe = true;
              mat.opacity = 0.5; // Dim wireframe
              mat.transparent = true;
              mat.depthWrite = false;
          } else if (settings.value.hiddenObjectMode === 'ghost') {
              mesh.visible = true;
              mat.wireframe = false;
              mat.transparent = true;
              mat.opacity = 0.1;
              mat.depthWrite = false;
          }
      } else {
          mesh.visible = true;
          // Restore original properties
          mat.wireframe = settings.value.wireframe || (data.originalWireframe ?? false);
          mat.transparent = data.originalTransparent ?? false;
          mat.depthWrite = true;
          
          if (data.type === 'Fenestration') {
             mat.opacity = settings.value.opacity;
          } else {
             mat.opacity = data.originalOpacity ?? 1;
          }

          // Update Color Mode for Surfaces
          // Already handled above
          /*
          if (data.type === 'BuildingSurface') {
             if (settings.value.colorMode === 'construction' && data.Construction) {
                 const colorHex = getConstructionColor(data.Construction);
                 mat.color.setHex(colorHex);
             } else {
                 // Reset to original color based on type
                 if (data.SurfaceType?.toUpperCase() === 'ROOF') mat.color.setHex(colors.value.roof);
                 else if (data.SurfaceType?.toUpperCase() === 'FLOOR') mat.color.setHex(colors.value.floor);
                 else mat.color.setHex(colors.value.wall);
             }
          }
          */
      }
      mat.needsUpdate = true;
    }
    
    // Edges visibility
    if ((child as any).isLine2) {
       applyEdgeMaterialSettings(child);
    }
  });

  if (axesHelperRef.value) {
    axesHelperRef.value.visible = settings.value.debugOn || settings.value.showAxes;
  }
  if (northArrowRef.value) {
    northArrowRef.value.visible = settings.value.debugOn || settings.value.showNorth;
  }

  applyShadowSettings();
};

const createGeometry = () => {
  const scene = sceneRef.value;
  if (!props.geometryData || !scene) return;
  
  // Clear previous models
  const objectsToRemove: THREE.Object3D[] = [];
  scene.traverse((child) => {
    if ((child as any).isMesh || (child as any).isLine2) {
      objectsToRemove.push(child);
    }
  });
  objectsToRemove.forEach(obj => scene.remove(obj));

  const { surfList, fenList, shadeList, zoneList, bldgCenter: center, bldgRadius: radius, boundary, northAxis = 0 } = props.geometryData;
  bldgCenter = center || [0, 0, 0];
  bldgRadius = radius || 100;

  // Add Axes Helper
  const axesHelper = new THREE.AxesHelper(bldgRadius * 1.5);
  axesHelper.position.set(bldgCenter[0], bldgCenter[1], bounds.value.minZ);
  axesHelperRef.value = axesHelper;
  scene.add(axesHelper);

  // Add North Arrow
  const arrowLength = bldgRadius * 1.5;
  const arrowPoints = [
    new THREE.Vector3(0, 0, 0),
    new THREE.Vector3(0, arrowLength, 0)
  ];
  const arrowGeom = new THREE.BufferGeometry().setFromPoints(arrowPoints);
  const arrowMat = new THREE.LineDashedMaterial({ color: 0x00ff00, linewidth: 2, dashSize: 2, gapSize: 1 });
  const northArrow = new THREE.Line(arrowGeom, arrowMat);
  northArrow.computeLineDistances();
  northArrow.position.set(bldgCenter[0], bldgCenter[1], bounds.value.minZ);
  northArrow.rotateZ(-northAxis * Math.PI / 180); // Assuming northAxis is clockwise from north
  northArrowRef.value = northArrow;
  scene.add(northArrow);

  // Add Shadow Catcher
  if (!shadowCatcherRef.value) {
    const shadowGeo = new THREE.PlaneGeometry(bldgRadius * 10, bldgRadius * 10);
    const shadowMat = new THREE.ShadowMaterial({ opacity: 0.5 });
    const shadowCatcher = new THREE.Mesh(shadowGeo, shadowMat);
    shadowCatcher.receiveShadow = true;
    shadowCatcherRef.value = shadowCatcher;
    scene.add(shadowCatcher);
  }
  updateThemeLighting();
  shadowCatcherRef.value.position.set(bldgCenter[0], bldgCenter[1], settings.value.shadowHeight);

  // Initialize bounds and zones if needed
  if (boundary) {
      bounds.value.minZ = Math.floor(boundary[0][2]);
      bounds.value.maxZ = Math.ceil(boundary[1][2]);
      if (settings.value.heightMin <= -1e8 || settings.value.heightMax >= 1e8) {
        settings.value.heightMin = bounds.value.minZ;
        settings.value.heightMax = bounds.value.maxZ;
      }
  }

  // Initialize zone visibility if empty
  if (zoneList && Object.keys(zoneVisibility.value).length === 0) {
    Object.keys(zoneList).forEach(z => {
      zoneVisibility.value[z] = true;
    });
  }

  // Materials with Polygon Offset to fix Z-fighting
  const polygonOffsetFactor = 1;
  const polygonOffsetUnits = 1;

  // Clone materials for instances to allow independent color changes if needed, 
  // but for 'construction' mode we update material color. 
  // Better to share materials and update meshes, but MeshPhongMaterial is shared.
  // We should clone material for each mesh if we want individual control, OR
  // Use a limited set of shared materials and update them? 
  // Actually, 'Color Mode' changes ALL surfaces. So we can just update the shared materials?
  // No, Construction mode assigns different colors to different surfaces.
  // So we need unique materials OR use Vertex Colors.
  // Using Vertex Colors is efficient.
  // But let's stick to cloning materials for now or just creating new ones.
  // Optimization: Create a material cache?
  // For now, let's create shared base materials.

  const matWall = new THREE.MeshPhongMaterial({ 
    color: colors.value.wall, 
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor,
    polygonOffsetUnits
  });
  const matRoof = new THREE.MeshPhongMaterial({ 
    color: colors.value.roof, 
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor,
    polygonOffsetUnits
  });
  const matFloor = new THREE.MeshPhongMaterial({ 
    color: colors.value.floor, 
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor,
    polygonOffsetUnits
  });
  const matWindow = new THREE.MeshPhongMaterial({ 
    color: colors.value.window, 
    transparent: true, 
    opacity: settings.value.opacity, 
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: -1,
    polygonOffsetUnits: -1
  });
  const matShade = new THREE.MeshPhongMaterial({ 
    color: colors.value.shade, 
    transparent: true, 
    opacity: 0.8, 
    side: THREE.DoubleSide,
    polygonOffset: true,
    polygonOffsetFactor: -2,
    polygonOffsetUnits: -2
  });
  
  const lineResolution = getLineMaterialResolution();
  const matEdge = new LineMaterial({ 
    color: isDark.value ? 0xaaaaaa : 0x000000, 
    linewidth: settings.value.edgeThicknessOn ? settings.value.edgeThickness : 1,
    resolution: new THREE.Vector2(lineResolution.width, lineResolution.height)
  });

  // Surfaces
  if (surfList) {
    for (const [surfName, surf] of Object.entries(surfList)) {
      const s = surf as any;
      let mat = matWall.clone(); // Clone to allow individual color changes
      if (s.SurfaceType?.toUpperCase() === 'ROOF') mat = matRoof.clone();
      if (s.SurfaceType?.toUpperCase() === 'FLOOR') mat = matFloor.clone();

      let holes = null;
      let vertList = s.Vertices;
      
      if (s.Fenestrations && s.Fenestrations.length > 0) {
        holes = [];
        s.Fenestrations.forEach((fenName: string) => {
          if (fenList && fenList[fenName]) {
            holes.push(vertList.length);
            vertList = vertList.concat(fenList[fenName].Vertices);
          }
        });
      }

      // Calculate Center Z
      let avgZ = 0;
      s.Vertices.forEach((v: number[]) => avgZ += v[2]);
      avgZ /= s.Vertices.length;

      try {
        const geom = triangulatedSurfacefromVertlist(vertList, holes);
        const mesh = new THREE.Mesh(geom, mat);
        mesh.name = surfName;
        mesh.userData = { 
            ...s, 
            type: 'BuildingSurface', 
            centerZ: avgZ,
            originalOpacity: mat.opacity,
            originalTransparent: mat.transparent,
            originalWireframe: mat.wireframe
        };
        mesh.castShadow = settings.value.shadows;
        mesh.receiveShadow = settings.value.shadows && settings.value.selfShadow;
        scene.add(mesh);

        // Edges
        const positions: number[] = [];
        s.Vertices.forEach((v: number[]) => positions.push(...v));
        positions.push(...s.Vertices[0]); // close loop
        
        const edgeGeom = new LineGeometry();
        edgeGeom.setPositions(positions);
        const line = new Line2(edgeGeom, matEdge);
        line.computeLineDistances();
        scene.add(line);
      } catch (e) {
        console.warn('Failed to triangulate surface:', surfName, e);
      }
    }
  }

  // Fenestrations
  if (fenList) {
    for (const [fenName, fen] of Object.entries(fenList)) {
      const f = fen as any;
      
      // Find parent zone for visibility logic
      let zoneName = null;
      if (f.BuildingSurfaceName && surfList && surfList[f.BuildingSurfaceName]) {
          zoneName = surfList[f.BuildingSurfaceName].ZoneName;
      }
      
      // Calculate Center Z
      let avgZ = 0;
      f.Vertices.forEach((v: number[]) => avgZ += v[2]);
      avgZ /= f.Vertices.length;

      try {
        const geom = triangulatedSurfacefromVertlist(f.Vertices);
        const mesh = new THREE.Mesh(geom, matWindow.clone());
        mesh.name = fenName;
        mesh.userData = { 
            ...f, 
            type: 'Fenestration', 
            ZoneName: zoneName, 
            centerZ: avgZ,
            originalOpacity: matWindow.opacity,
            originalTransparent: matWindow.transparent,
            originalWireframe: matWindow.wireframe
        };
        scene.add(mesh);
      } catch (e) {
        console.warn('Failed to triangulate fenestration:', fenName, e);
      }
    }
  }

  // Shading
  if (shadeList) {
    for (const [shadeName, shade] of Object.entries(shadeList)) {
      const sh = shade as any;
      
      // Calculate Center Z
      let avgZ = 0;
      sh.Vertices.forEach((v: number[]) => avgZ += v[2]);
      avgZ /= sh.Vertices.length;

      try {
        const geom = triangulatedSurfacefromVertlist(sh.Vertices);
        const mesh = new THREE.Mesh(geom, matShade.clone());
        mesh.name = shadeName;
        mesh.userData = { 
            ...sh, 
            type: 'Shading', 
            centerZ: avgZ,
            originalOpacity: matShade.opacity,
            originalTransparent: matShade.transparent,
            originalWireframe: matShade.wireframe
        };
        scene.add(mesh);
      } catch (e) {
        console.warn('Failed to triangulate shade:', shadeName, e);
      }
    }
  }

  resetCamera();
  updateVisibility(); // Apply initial visibility
};

// Helper to get color for construction
const getConstructionColor = (name: string) => {
  if (!constructionColors.value[name]) {
    // Generate random pastel color
    const hue = Math.floor(Math.random() * 360);
    const color = new THREE.Color(`hsl(${hue}, 70%, 70%)`);
    constructionColors.value[name] = color.getHex();
  }
  return constructionColors.value[name];
};

function getCameraFitDistance(radius: number, fovDegrees: number, aspect: number) {
  const safeRadius = Math.max(1, radius);
  const safeAspect = Math.max(0.1, aspect || 1);
  const verticalFov = THREE.MathUtils.degToRad(clamp(fovDegrees, 15, 80));
  const horizontalFov = 2 * Math.atan(Math.tan(verticalFov * 0.5) * safeAspect);
  const fitFov = Math.max(THREE.MathUtils.degToRad(1), Math.min(verticalFov, horizontalFov));
  return (safeRadius / Math.sin(fitFov * 0.5)) * CAMERA_FIT_PADDING;
}

function fitCameraToBuilding() {
  if (!cameraRef.value || !controlsRef.value) return;

  const radius = Math.max(1, bldgRadius);
  const aspect = canvasHost.value
    ? canvasHost.value.clientWidth / Math.max(1, canvasHost.value.clientHeight)
    : cameraRef.value.aspect;
  const distance = getCameraFitDistance(radius, settings.value.cameraFov, aspect);

  cameraRef.value.far = Math.max(MIN_CAMERA_FAR, distance + radius * CAMERA_FAR_PADDING_MULTIPLIER);
  settings.value.cameraFar = cameraRef.value.far;
  cameraRef.value.updateProjectionMatrix();

  settings.value.maxZoom = Math.max(
    settings.value.maxZoom,
    distance * CAMERA_MAX_DISTANCE_MULTIPLIER,
  );
  applyOrbitInteractionProfile(controlsRef.value);
  controlsRef.value.target.set(bldgCenter[0], bldgCenter[1], bldgCenter[2]);
  cameraRef.value.position.set(
    bldgCenter[0] + cameraFitDirection.x * distance,
    bldgCenter[1] + cameraFitDirection.y * distance,
    bldgCenter[2] + cameraFitDirection.z * distance,
  );
  cameraRef.value.up.set(0, 0, 1);
  cameraRef.value.lookAt(bldgCenter[0], bldgCenter[1], bldgCenter[2]);
  controlsRef.value.update();
}

const resetCamera = () => {
  fitCameraToBuilding();
};

const snapCamera = () => {
  if (!cameraRef.value || !controlsRef.value) return;
  const snap = Math.PI / 4;
  const azm = controlsRef.value.getAzimuthalAngle();
  const polar = controlsRef.value.getPolarAngle();

  const snappedAzm = Math.round(azm / snap) * snap;
  const snappedPolar = Math.round(polar / snap) * snap;

  const target = controlsRef.value.target.clone();
  const distance = cameraRef.value.position.distanceTo(target);
  const radiusXY = distance * Math.sin(snappedPolar);

  cameraRef.value.position.x = target.x + radiusXY * Math.sin(snappedAzm);
  cameraRef.value.position.y = target.y + radiusXY * Math.cos(snappedAzm);
  cameraRef.value.position.z = target.z + distance * Math.cos(snappedPolar);

  cameraRef.value.lookAt(target);
  controlsRef.value.update();
};

const takeScreenshot = () => {
  if (!rendererRef.value || !sceneRef.value || !cameraRef.value) return;
  rendererRef.value.render(sceneRef.value, cameraRef.value);
  const dataURL = rendererRef.value.domElement.toDataURL('image/png');
  const link = document.createElement('a');
  link.download = 'epshape-screenshot.png';
  link.href = dataURL;
  link.click();
};

const handleResize = () => {
  if (!canvasHost.value || !cameraRef.value || !rendererRef.value) return;
  const width = canvasHost.value.clientWidth;
  const height = canvasHost.value.clientHeight;
  cameraRef.value.aspect = width / height;
  cameraRef.value.updateProjectionMatrix();
  rendererRef.value.setSize(width, height);
  applyOrbitInteractionProfile();
  sceneRef.value?.traverse((child) => {
    if ((child as any).isLine2) applyEdgeMaterialSettings(child);
  });
};

const onMouseMove = (event: MouseEvent) => {
  if (!canvasHost.value || !cameraRef.value || !sceneRef.value) return;
  if (isDraggingCamera) {
    hoveredObject.value = null;
    tooltipData.value = null;
    return;
  }
  const now = performance.now();
  if (now - lastHoverSampleAt < HOVER_SAMPLE_INTERVAL_MS) return;
  lastHoverSampleAt = now;

  const rect = canvasHost.value.getBoundingClientRect();
  mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
  mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

  raycaster.setFromCamera(mouse, cameraRef.value);

  const intersects = raycaster.intersectObjects(sceneRef.value.children);
  
  if (intersects.length > 0) {
    // Find first mesh that is not a line
    const hit = intersects.find(i => (i.object as any).isMesh);
    if (hit) {
      hoveredObject.value = hit.object.userData;
      
      // Tooltip position
      if (tooltip.value) {
        tooltip.value.style.left = `${event.clientX + 15}px`;
        tooltip.value.style.top = `${event.clientY + 15}px`;
        tooltipData.value = {
          name: hit.object.name,
          ...hit.object.userData
        };
      }
    } else {
      hoveredObject.value = null;
      tooltipData.value = null;
    }
  } else {
    hoveredObject.value = null;
    tooltipData.value = null;
  }
};

const onMouseClick = () => {
  // Can implement selection here
};

const isShiftDown = ref(false);

const handleKeydown = (event: KeyboardEvent) => {
  if (event.key === 'Shift') isShiftDown.value = true;
  
  // Ignore if typing in an input
  if ((event.target as HTMLElement).tagName === 'INPUT') return;

  // Ctrl+Shift+C: Copy Settings
  if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'c') {
    event.preventDefault();
    const configStr = JSON.stringify(settings.value);
    navigator.clipboard.writeText(configStr).then(() => {
      alert(t('viewer3d.notices.settingsCopied'));
    });
    return;
  }

  // Ctrl+Shift+V: Paste Settings
  if (event.ctrlKey && event.shiftKey && event.key.toLowerCase() === 'v') {
    event.preventDefault();
    navigator.clipboard.readText().then(text => {
      try {
        const config = JSON.parse(text);
        Object.assign(settings.value, config);
        alert(t('viewer3d.notices.settingsApplied'));
      } catch (e) {
        alert(t('viewer3d.notices.invalidSettings'));
      }
    });
    return;
  }

  switch(event.key.toLowerCase()) {
    case 'a':
      toggleRotation();
      break;
    case 'x':
      toggleSlice();
      break;
    case 'r':
      resetCamera();
      break;
    case 's':
      takeScreenshot();
      break;
    case '/':
      event.preventDefault();
      showCommandPrompt.value = true;
      setTimeout(() => {
        commandInputRef.value?.focus();
      }, 50);
      break;
  }
};

const handleKeyup = (event: KeyboardEvent) => {
  if (event.key === 'Shift') isShiftDown.value = false;
};

const applyViewerSettings = () => {
  applyOrbitInteractionProfile();
  updateVisibility();
};

// Watchers
watch(() => props.geometryData, createGeometry, { deep: true });
watch([isDark, theme], () => {
  updateBackground();
  updateThemeLighting();
  // createGeometry(); // No need to recreate, just update edge colors if we had dynamic edge colors
  // But edges use LineMaterial with color. We can update material color.
  if (sceneRef.value) {
      sceneRef.value.traverse((child) => {
          if ((child as any).isLine2) {
             (child as any).material.color.setHex(isDark.value ? 0xaaaaaa : 0x000000);
             applyEdgeMaterialSettings(child);
          }
      });
  }
});
// Watch settings and zoneVisibility to update visibility
watch(settings, applyViewerSettings, { deep: true });
watch(zoneVisibility, updateVisibility, { deep: true });
watch(colors, updateVisibility, { deep: true });

onMounted(() => {
  initScene();
});

onUnmounted(() => {
  window.removeEventListener('resize', handleResize);
  window.removeEventListener('keydown', handleKeydown);
  window.removeEventListener('keyup', handleKeyup);
  stopPanelDrag();
  cancelAnimationFrame(animationId);
  if (rendererRef.value) {
    rendererRef.value.dispose();
  }
});
</script>

<template>
  <div ref="viewerRoot" class="epshape-viewer relative w-full h-full overflow-hidden">
    <div ref="canvasHost" class="absolute inset-0"></div>

    <div v-if="tooltipData" ref="tooltip" class="fixed z-50 p-2 bg-black/80 text-white text-xs rounded pointer-events-none max-w-xs shadow-lg backdrop-blur-sm border border-white/10">
      <div class="font-bold border-b border-white/20 mb-1 pb-1">{{ tooltipData.name }}</div>
      <div v-for="(val, key) in tooltipData" :key="key">
        <div v-if="String(key) !== 'name' && String(key) !== 'Vertices' && String(key) !== 'Fenestrations'" class="flex justify-between gap-4">
          <span class="opacity-70 capitalize">{{ key }}:</span>
          <span>{{ val }}</span>
        </div>
      </div>
    </div>

    <div v-if="showCommandPrompt" class="absolute bottom-4 left-1/2 -translate-x-1/2 z-40 w-[520px] max-w-[92vw]">
      <input
        ref="commandInputRef"
        v-model="commandInput"
        @keyup.enter="executeCommand"
        @keyup.esc="showCommandPrompt = false"
        type="text"
        class="w-full bg-white/90 dark:bg-[#1b1b1b]/90 text-black dark:text-white px-4 py-2 rounded-lg shadow-xl backdrop-blur-md border border-black/10 dark:border-white/10 outline-none focus:ring-2 focus:ring-[#00cfc8]/40"
        :placeholder="t('viewer3d.command.placeholder')"
      />
    </div>

    <div class="absolute top-2 right-2 z-40 flex gap-2">
      <button id="SettingsBtn" class="epshape-btn epshape-btn-settings" :title="t('viewer3d.toolbar.settings')" @click="togglePanel('settings')"></button>
      <button id="VisibilityBtn" class="epshape-btn epshape-btn-visibility" :title="t('viewer3d.toolbar.visibility')" @click="togglePanel('visibility')"></button>
      <button id="SaveBtn" class="epshape-btn epshape-btn-save" :title="t('viewer3d.toolbar.exportImage')" @click="exportImage"></button>
      <button id="HelpBtn" class="epshape-btn epshape-btn-help" :title="t('viewer3d.toolbar.help')" @click="togglePanel('help')"></button>
      <button
        v-if="props.showFullscreenButton"
        id="MaximizeBtn"
        class="epshape-btn"
        :class="props.isMaximized ? 'epshape-btn-minimize' : 'epshape-btn-maximize'"
        :title="props.isMaximized ? t('viewer3d.toolbar.exitFullscreen') : t('viewer3d.toolbar.fullscreen')"
        @click="emit('toggle-maximize')"
      ></button>
    </div>

    <div v-if="showVisibilityPanel" id="VisibilityPanel" data-panel-tag="visibility" class="absolute z-40 w-[350px] rounded-xl bg-[var(--app-panel)] text-[var(--app-text)] backdrop-blur-md shadow-2xl border border-[color:var(--app-border)]" :style="panelStyle('visibility')">
      <div class="flex cursor-move items-center justify-between px-4 py-3 border-b border-[color:var(--app-border)]" @pointerdown="startPanelDrag('visibility', $event)">
        <div class="font-semibold">{{ t('viewer3d.visibility.title') }}</div>
        <button class="h-7 w-7 rounded bg-black/5 dark:bg-white/10 text-sm" :title="t('viewer3d.common.close')" :aria-label="t('viewer3d.common.close')" @pointerdown.stop @click="showVisibilityPanel = false">x</button>
      </div>

      <div class="p-4 space-y-4 text-sm">
        <div>
          <div class="text-xs font-semibold uppercase tracking-wider opacity-70 mb-2">{{ t('viewer3d.visibility.filterBy') }}</div>
          <div class="flex gap-2">
            <button class="flex-1 px-2 py-1 rounded border border-black/10 dark:border-white/10" :class="visFilterType === 'zones' ? 'bg-[#00cfc8]/15 border-[#00cfc8]/40' : 'bg-black/5 dark:bg-white/5'" @click="changeVisFilter('zones')" :disabled="visFilterType === 'zones'">{{ t('viewer3d.visibility.zones') }}</button>
            <button class="flex-1 px-2 py-1 rounded border border-black/10 dark:border-white/10" :class="visFilterType === 'height' ? 'bg-[#00cfc8]/15 border-[#00cfc8]/40' : 'bg-black/5 dark:bg-white/5'" @click="changeVisFilter('height')" :disabled="visFilterType === 'height'">{{ t('viewer3d.visibility.height') }}</button>
            <button class="flex-1 px-2 py-1 rounded border border-black/10 dark:border-white/10" :class="visFilterType === 'both' ? 'bg-[#00cfc8]/15 border-[#00cfc8]/40' : 'bg-black/5 dark:bg-white/5'" @click="changeVisFilter('both')" :disabled="visFilterType === 'both'">{{ t('viewer3d.visibility.both') }}</button>
          </div>
        </div>

        <div v-if="visFilterType === 'zones' || visFilterType === 'both'" class="space-y-2">
          <div class="flex items-center justify-between">
            <div class="text-xs font-semibold uppercase tracking-wider opacity-70">{{ t('viewer3d.visibility.zones') }}</div>
            <div class="flex gap-2">
              <button class="px-2 py-1 rounded bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10" @click="changeZoneAll(true)">{{ t('viewer3d.visibility.showAll') }}</button>
              <button class="px-2 py-1 rounded bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10" @click="changeZoneAll(false)">{{ t('viewer3d.visibility.hideAll') }}</button>
            </div>
          </div>
          <div class="max-h-40 overflow-y-auto space-y-1 pr-1">
            <label v-for="(_visible, zoneName) in zoneVisibility" :key="zoneName" class="flex items-center gap-2">
              <input type="checkbox" v-model="zoneVisibility[zoneName]" class="accent-[#00cfc8]">
              <span class="truncate" :title="zoneName">{{ zoneName }}</span>
            </label>
          </div>
        </div>

        <div v-if="visFilterType === 'height' || visFilterType === 'both'" class="space-y-2">
          <div class="flex items-center justify-between">
            <div class="text-xs font-semibold uppercase tracking-wider opacity-70">{{ t('viewer3d.visibility.heightRange') }}</div>
            <button class="px-2 py-1 rounded bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10" @click="resetHeightRange">{{ t('viewer3d.actions.reset') }}</button>
          </div>
          <div class="space-y-2">
            <div class="flex items-center gap-2">
              <div class="w-10 text-xs opacity-70">{{ t('viewer3d.visibility.min') }}</div>
              <input type="range" class="w-full" :min="bounds.minZ" :max="bounds.maxZ" :step="0.01" :value="settings.heightMin" @input="updateHeightMin(parseFloat(($event.target as HTMLInputElement).value))">
              <input type="number" class="w-24 px-2 py-1 rounded bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10" :min="bounds.minZ" :max="bounds.maxZ" :value="settings.heightMin" @change="updateHeightMin(parseFloat(($event.target as HTMLInputElement).value))">
            </div>
            <div class="flex items-center gap-2">
              <div class="w-10 text-xs opacity-70">{{ t('viewer3d.visibility.max') }}</div>
              <input type="range" class="w-full" :min="bounds.minZ" :max="bounds.maxZ" :step="0.01" :value="settings.heightMax" @input="updateHeightMax(parseFloat(($event.target as HTMLInputElement).value))">
              <input type="number" class="w-24 px-2 py-1 rounded bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10" :min="bounds.minZ" :max="bounds.maxZ" :value="settings.heightMax" @change="updateHeightMax(parseFloat(($event.target as HTMLInputElement).value))">
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-if="showSettingsPanel" id="SettingsPanel" data-panel-tag="settings" class="absolute z-40 w-[350px] rounded-xl bg-[var(--app-panel)] text-[var(--app-text)] backdrop-blur-md shadow-2xl border border-[color:var(--app-border)]" :style="panelStyle('settings')">
      <div class="flex cursor-move items-center justify-between px-4 py-3 border-b border-[color:var(--app-border)]" @pointerdown="startPanelDrag('settings', $event)">
        <div class="font-semibold">{{ t('viewer3d.settings.title') }}</div>
        <button class="h-7 w-7 rounded bg-black/5 dark:bg-white/10 text-sm" :title="t('viewer3d.common.close')" :aria-label="t('viewer3d.common.close')" @pointerdown.stop @click="showSettingsPanel = false">x</button>
      </div>

      <div class="p-4 space-y-4 text-sm max-h-[70vh] overflow-y-auto">
        <div>
          <div class="text-xs font-semibold uppercase tracking-wider opacity-70 mb-2">{{ t('viewer3d.settings.visual') }}</div>
          <label class="flex items-center justify-between">
            <span>{{ t('viewer3d.settings.shading') }}</span>
            <input type="checkbox" v-model="settings.showShading" class="accent-[#00cfc8]">
          </label>
          <label class="flex items-center justify-between mt-2">
            <span>{{ t('viewer3d.settings.edgeThickness') }}</span>
            <input type="checkbox" v-model="settings.edgeThicknessOn" class="accent-[#00cfc8]">
          </label>
          <div v-if="settings.edgeThicknessOn" class="mt-1">
            <input type="range" v-model.number="settings.edgeThickness" min="1" max="10" step="0.5" class="w-full">
          </div>
          <div class="mt-2 flex items-center justify-between">
            <span>{{ t('viewer3d.settings.hiddenObjects') }}</span>
            <select v-model="settings.hiddenObjectMode" class="px-2 py-1 rounded bg-black/5 dark:bg-white/5 border border-black/10 dark:border-white/10">
              <option value="disable">{{ t('viewer3d.settings.hiddenModes.hide') }}</option>
              <option value="wireframe">{{ t('viewer3d.settings.hiddenModes.wire') }}</option>
              <option value="ghost">{{ t('viewer3d.settings.hiddenModes.ghost') }}</option>
            </select>
          </div>
          <label class="flex items-center justify-between mt-2">
            <span>{{ t('viewer3d.settings.shadow') }}</span>
            <input type="checkbox" v-model="settings.shadows" class="accent-[#00cfc8]">
          </label>
          <label class="flex items-center justify-between mt-2">
            <span>{{ t('viewer3d.settings.transparency') }}</span>
            <input type="checkbox" v-model="settings.transparencyOn" class="accent-[#00cfc8]">
          </label>
          <label class="flex items-center justify-between mt-2">
            <span>{{ t('viewer3d.settings.debug') }}</span>
            <input type="checkbox" v-model="settings.debugOn" class="accent-[#00cfc8]">
          </label>
          <div class="mt-3">
            <div class="flex items-center justify-between gap-3">
              <span>{{ t('viewer3d.settings.navigationSensitivity') }}</span>
              <span class="w-10 text-right text-xs opacity-70">{{ settings.navigationSensitivity.toFixed(2) }}</span>
            </div>
            <input
              type="range"
              v-model.number="settings.navigationSensitivity"
              :min="NAVIGATION_SENSITIVITY_MIN"
              :max="NAVIGATION_SENSITIVITY_MAX"
              step="0.05"
              class="mt-1 w-full"
            >
          </div>
        </div>

        <div>
          <div class="text-xs font-semibold uppercase tracking-wider opacity-70 mb-2">{{ t('viewer3d.settings.materialsBy') }}</div>
          <div class="flex gap-2">
            <button class="flex-1 px-2 py-1 rounded border border-black/10 dark:border-white/10" :class="settings.colorMode === 'surfaceType' ? 'bg-[#00cfc8]/15 border-[#00cfc8]/40' : 'bg-black/5 dark:bg-white/5'" @click="settings.colorMode = 'surfaceType'">{{ t('viewer3d.settings.surfaceType') }}</button>
            <button class="flex-1 px-2 py-1 rounded border border-black/10 dark:border-white/10" :class="settings.colorMode === 'construction' ? 'bg-[#00cfc8]/15 border-[#00cfc8]/40' : 'bg-black/5 dark:bg-white/5'" @click="settings.colorMode = 'construction'">{{ t('viewer3d.settings.construction') }}</button>
          </div>
          <div class="mt-2">
            <div class="flex items-center justify-between">
              <span>{{ t('viewer3d.settings.windowOpacity') }}</span>
              <input type="range" v-model.number="settings.opacity" min="0" max="1" step="0.05" class="w-40">
            </div>
          </div>
        </div>

        <div v-if="settings.shadows" class="space-y-2">
          <div class="text-xs font-semibold uppercase tracking-wider opacity-70">{{ t('viewer3d.settings.shadows') }}</div>
          <label class="flex items-center justify-between">
            <span>{{ t('viewer3d.settings.selfShadow') }}</span>
            <input type="checkbox" v-model="settings.selfShadow" class="accent-[#00cfc8]">
          </label>
          <div class="flex items-center justify-between">
            <span>{{ t('viewer3d.settings.altitude') }}</span>
            <input type="range" v-model.number="settings.shadowAlt" min="0" max="90" step="1" class="w-40">
          </div>
          <div class="flex items-center justify-between">
            <span>{{ t('viewer3d.settings.azimuth') }}</span>
            <input type="range" v-model.number="settings.shadowAzm" min="-180" max="180" step="1" class="w-40">
          </div>
          <div class="flex items-center justify-between">
            <span>{{ t('viewer3d.settings.height') }}</span>
            <input type="range" v-model.number="settings.shadowHeight" :min="bounds.minZ - 10" :max="bounds.maxZ" step="0.5" class="w-40">
          </div>
        </div>
      </div>
    </div>

    <div v-if="showHelpPanel" id="HelpPanel" data-panel-tag="help" class="absolute z-40 w-[500px] max-w-[92vw] rounded-xl bg-[var(--app-panel)] text-[var(--app-text)] backdrop-blur-md shadow-2xl border border-[color:var(--app-border)]" :style="panelStyle('help')">
      <div class="flex cursor-move items-center justify-between px-4 py-3 border-b border-[color:var(--app-border)]" @pointerdown="startPanelDrag('help', $event)">
        <div class="font-semibold">{{ t('viewer3d.help.title') }}</div>
        <button class="h-7 w-7 rounded bg-black/5 dark:bg-white/10 text-sm" :title="t('viewer3d.common.close')" :aria-label="t('viewer3d.common.close')" @pointerdown.stop @click="showHelpPanel = false">x</button>
      </div>
      <div class="p-4 text-sm space-y-4 max-h-[70vh] overflow-y-auto">
        <div>
          <div class="font-semibold mb-2">{{ t('viewer3d.help.sections.scope.title') }}</div>
          <p class="text-[var(--app-text-muted)]">
            {{ t('viewer3d.help.sections.scope.body') }}
          </p>
        </div>
        <div>
          <div class="font-semibold mb-2">{{ t('viewer3d.help.sections.toolbar.title') }}</div>
          <ul class="list-disc pl-5 space-y-1 opacity-90">
            <li>{{ t('viewer3d.help.sections.toolbar.settings') }}</li>
            <li>{{ t('viewer3d.help.sections.toolbar.visibility') }}</li>
            <li>{{ t('viewer3d.help.sections.toolbar.exportImage') }}</li>
            <li>{{ t('viewer3d.help.sections.toolbar.help') }}</li>
            <li>{{ t('viewer3d.help.sections.toolbar.fullscreen') }}</li>
          </ul>
        </div>
        <div>
          <div class="font-semibold mb-2">{{ t('viewer3d.help.sections.mouse.title') }}</div>
          <ul class="list-disc pl-5 space-y-1 opacity-90">
            <li>{{ t('viewer3d.help.sections.mouse.left') }}</li>
            <li>{{ t('viewer3d.help.sections.mouse.shiftLeft') }}</li>
            <li>{{ t('viewer3d.help.sections.mouse.pan') }}</li>
            <li>{{ t('viewer3d.help.sections.mouse.wheel') }}</li>
          </ul>
        </div>
        <div>
          <div class="font-semibold mb-2">{{ t('viewer3d.help.sections.keyboard.title') }}</div>
          <ul class="list-disc pl-5 space-y-1 opacity-90">
            <li>{{ t('viewer3d.help.sections.keyboard.reset') }}</li>
            <li>{{ t('viewer3d.help.sections.keyboard.exportImage') }}</li>
            <li>{{ t('viewer3d.help.sections.keyboard.command') }}</li>
            <li>{{ t('viewer3d.help.sections.keyboard.copy') }}</li>
            <li>{{ t('viewer3d.help.sections.keyboard.paste') }}</li>
          </ul>
        </div>
        <div>
          <div class="font-semibold mb-2">{{ t('viewer3d.help.sections.command.title') }}</div>
          <ul class="list-disc pl-5 space-y-1 opacity-90">
            <li>{{ t('viewer3d.help.sections.command.help') }}</li>
            <li>{{ t('viewer3d.help.sections.command.shadowAlt') }}</li>
            <li>{{ t('viewer3d.help.sections.command.shadowAzm') }}</li>
            <li>{{ t('viewer3d.help.sections.command.selfShadow') }}</li>
            <li>{{ t('viewer3d.help.sections.command.cameraFov') }}</li>
          </ul>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.epshape-btn {
  height: 36px;
  width: 36px;
  border-radius: 9999px;
  background-color: rgba(0, 0, 0, 0.3);
  border: 1px solid rgba(255, 255, 255, 0.12);
  backdrop-filter: blur(6px);
  background-repeat: no-repeat;
  background-position: center;
  background-size: 18px 18px;
}

.epshape-btn:hover {
  background-color: rgba(0, 0, 0, 0.45);
}

.epshape-btn-save {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z'/%3E%3Cpolyline points='17 21 17 13 7 13 7 21'/%3E%3Cpolyline points='7 3 7 8 15 8'/%3E%3C/svg%3E");
}

.epshape-btn-visibility {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M2 12s3-7 10-7 10 7 10 7-3 7-10 7S2 12 2 12z'/%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3C/svg%3E");
}

.epshape-btn-settings {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M12.22 2h-.44a2 2 0 0 0-2 2v.18a2 2 0 0 1-1 1.73l-.43.25a2 2 0 0 1-2 0l-.15-.08a2 2 0 0 0-2.73.73l-.22.38a2 2 0 0 0 .73 2.73l.15.1a2 2 0 0 1 1 1.72v.51a2 2 0 0 1-1 1.74l-.15.09a2 2 0 0 0-.73 2.73l.22.38a2 2 0 0 0 2.73.73l.15-.08a2 2 0 0 1 2 0l.43.25a2 2 0 0 1 1 1.73V20a2 2 0 0 0 2 2h.44a2 2 0 0 0 2-2v-.18a2 2 0 0 1 1-1.73l.43-.25a2 2 0 0 1 2 0l.15.08a2 2 0 0 0 2.73-.73l.22-.39a2 2 0 0 0-.73-2.73l-.15-.1a2 2 0 0 1-1-1.72v-.51a2 2 0 0 1 1-1.74l.15-.09a2 2 0 0 0 .73-2.73l-.22-.38a2 2 0 0 0-2.73-.73l-.15.08a2 2 0 0 1-2 0l-.43-.25a2 2 0 0 1-1-1.73V4a2 2 0 0 0-2-2z'/%3E%3Ccircle cx='12' cy='12' r='3'/%3E%3C/svg%3E");
}

.epshape-btn-help {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'/%3E%3Cpath d='M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3'/%3E%3Cpath d='M12 17h.01'/%3E%3C/svg%3E");
}

.epshape-btn-maximize {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M15 3h6v6'/%3E%3Cpath d='M9 21H3v-6'/%3E%3Cpath d='M21 3l-7 7'/%3E%3Cpath d='M3 21l7-7'/%3E%3C/svg%3E");
}

.epshape-btn-minimize {
  background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M4 14h6v6'/%3E%3Cpath d='M20 10h-6V4'/%3E%3Cpath d='M14 10l7-7'/%3E%3Cpath d='M3 21l6-6'/%3E%3C/svg%3E");
}
</style>
