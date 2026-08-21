export interface GeometryData {
  zoneList: Record<string, unknown>
  surfList: Record<string, unknown>
  fenList: Record<string, unknown>
  shadeList: Record<string, unknown>
  boundary: number[][]
  bldgCenter: number[]
  bldgRadius: number
}

export interface ChartSeries {
  key: string
  label: string
  unit: string
  values: Array<number | null>
}

export interface ChartGroup {
  labels: string[]
  series: ChartSeries[]
}

export interface SimulationResult {
  row_count: number
  sampled_count: number
  timesteps_per_hour: number
  zone_count: number
  weather: ChartGroup
  indoor: ChartGroup
  energy: ChartGroup
}

interface FailurePayload {
  message?: string
  hint?: string
}

async function readResponse<T>(response: Response): Promise<T> {
  if (response.ok) return (await response.json()) as T
  const payload = (await response.json().catch(() => ({}))) as FailurePayload
  const message = [payload.message, payload.hint].filter(Boolean).join(' ')
  throw new Error(message || 'The request could not be completed.')
}

export async function renderGeometry(idfFile: File): Promise<GeometryData> {
  const form = new FormData()
  form.append('idf_file', idfFile)
  const response = await fetch('/api/render', { method: 'POST', body: form })
  const payload = await readResponse<{ geometry: GeometryData }>(response)
  return payload.geometry
}

export async function runSimulation(
  idfFile: File,
  epwFile: File,
): Promise<SimulationResult> {
  const form = new FormData()
  form.append('idf_file', idfFile)
  form.append('epw_file', epwFile)
  const response = await fetch('/api/simulation', { method: 'POST', body: form })
  return readResponse<SimulationResult>(response)
}
