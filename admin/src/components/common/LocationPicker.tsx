import { useState, useEffect, useRef } from 'react'
import { Box, TextField, Typography, ToggleButtonGroup, ToggleButton, Button, Alert, CircularProgress } from '@mui/material'
import { MapContainer, TileLayer, Marker, useMapEvents, useMap } from 'react-leaflet'
import SearchIcon from '@mui/icons-material/Search'
import CheckIcon from '@mui/icons-material/Check'
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import type { Location } from '@/types'
import { patientService, GeocodePreviewResponse } from '@/services/patientService'

// Fix for default marker icon in Leaflet with Webpack
delete (L.Icon.Default.prototype as any)._getIconUrl
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
})

type LocationMode = 'coordinates' | 'address'

interface LocationPickerProps {
  value?: Location
  address?: string
  onChange: (location: Location) => void
  onAddressChange?: (address: string) => void
  label?: string
  error?: boolean
  helperText?: string
  allowAddressInput?: boolean
}

// Component to handle map clicks (for coordinates mode)
function MapClickHandler({ onClick }: { onClick: (lat: number, lng: number) => void }) {
  useMapEvents({
    click: (e) => {
      onClick(e.latlng.lat, e.latlng.lng)
    },
  })
  return null
}

// Component to handle draggable marker (for address mode)
function DraggableMarker({
  position,
  onDragEnd
}: {
  position: [number, number]
  onDragEnd: (lat: number, lng: number) => void
}) {
  const markerRef = useRef<L.Marker>(null)

  const eventHandlers = {
    dragend() {
      const marker = markerRef.current
      if (marker != null) {
        const pos = marker.getLatLng()
        onDragEnd(pos.lat, pos.lng)
      }
    },
  }

  return (
    <Marker
      draggable={true}
      eventHandlers={eventHandlers}
      position={position}
      ref={markerRef}
    />
  )
}

// Component to recenter map when location changes
function MapRecenter({ center }: { center: [number, number] }) {
  const map = useMap()
  useEffect(() => {
    map.setView(center, 15)
  }, [center, map])
  return null
}

export default function LocationPicker({
  value,
  address: initialAddress,
  onChange,
  onAddressChange,
  label = 'Ubicación',
  error = false,
  helperText,
  allowAddressInput = true,
}: LocationPickerProps) {
  const [latitude, setLatitude] = useState(value?.latitude?.toString() || '')
  const [longitude, setLongitude] = useState(value?.longitude?.toString() || '')
  const [addressInput, setAddressInput] = useState(initialAddress || '')
  const [mode, setMode] = useState<LocationMode>(
    initialAddress ? 'address' : 'coordinates'
  )

  // Geocoding state
  const [isGeocoding, setIsGeocoding] = useState(false)
  const [geocodeError, setGeocodeError] = useState<string | null>(null)
  const [geocodeResult, setGeocodeResult] = useState<GeocodePreviewResponse | null>(null)
  const [tempLocation, setTempLocation] = useState<[number, number] | null>(null)
  const [showMap, setShowMap] = useState(false)

  // Default center (Santiago, Chile)
  const defaultCenter: [number, number] = [-33.4489, -70.6693]
  const center: [number, number] = value ? [value.latitude, value.longitude] : defaultCenter

  useEffect(() => {
    if (value) {
      setLatitude(value.latitude.toString())
      setLongitude(value.longitude.toString())
    }
  }, [value])

  useEffect(() => {
    if (initialAddress) {
      setAddressInput(initialAddress)
    }
  }, [initialAddress])

  const handleLatitudeChange = (lat: string) => {
    setLatitude(lat)
    const latNum = parseFloat(lat)
    const lngNum = parseFloat(longitude)
    if (!isNaN(latNum) && !isNaN(lngNum) && latNum >= -90 && latNum <= 90) {
      onChange({ latitude: latNum, longitude: lngNum })
    }
  }

  const handleLongitudeChange = (lng: string) => {
    setLongitude(lng)
    const latNum = parseFloat(latitude)
    const lngNum = parseFloat(lng)
    if (!isNaN(latNum) && !isNaN(lngNum) && lngNum >= -180 && lngNum <= 180) {
      onChange({ latitude: latNum, longitude: lngNum })
    }
  }

  const handleMapClick = (lat: number, lng: number) => {
    setLatitude(lat.toFixed(6))
    setLongitude(lng.toFixed(6))
    onChange({ latitude: lat, longitude: lng })
  }

  const handleAddressInputChange = (address: string) => {
    setAddressInput(address)
    if (onAddressChange) {
      onAddressChange(address)
    }
  }

  const handleModeChange = (_event: React.MouseEvent<HTMLElement>, newMode: LocationMode | null) => {
    if (newMode !== null) {
      setMode(newMode)
      // Reset geocoding state when switching modes
      setShowMap(false)
      setGeocodeResult(null)
      setGeocodeError(null)
      setTempLocation(null)
    }
  }

  // Handle geocoding button click
  const handleGeocodeSearch = async () => {
    if (!addressInput || addressInput.trim() === '') {
      setGeocodeError('Por favor ingrese una dirección')
      return
    }

    setIsGeocoding(true)
    setGeocodeError(null)
    setGeocodeResult(null)

    try {
      const result = await patientService.geocodePreview(addressInput)
      setGeocodeResult(result)
      setTempLocation([result.latitude, result.longitude])
      setShowMap(true)
      setGeocodeError(null)
    } catch (err: any) {
      const errorMessage = err?.response?.data?.detail || 'Error al geocodificar la dirección. Verifique que sea válida.'
      setGeocodeError(errorMessage)
      setShowMap(false)
    } finally {
      setIsGeocoding(false)
    }
  }

  // Handle marker drag in address mode
  const handleMarkerDrag = (lat: number, lng: number) => {
    setTempLocation([lat, lng])
  }

  // Confirm geocoded location
  const handleConfirmLocation = () => {
    if (tempLocation) {
      onChange({ latitude: tempLocation[0], longitude: tempLocation[1] })
      if (onAddressChange && geocodeResult) {
        onAddressChange(geocodeResult.formatted_address)
      }
      // Update display values
      setLatitude(tempLocation[0].toFixed(6))
      setLongitude(tempLocation[1].toFixed(6))
    }
  }

  return (
    <Box sx={{ mb: 2 }}>
      <Typography variant="subtitle2" gutterBottom>
        {label}
      </Typography>

      {/* Mode Toggle */}
      {allowAddressInput && (
        <Box sx={{ mb: 2 }}>
          <ToggleButtonGroup
            value={mode}
            exclusive
            onChange={handleModeChange}
            size="small"
            fullWidth
          >
            <ToggleButton value="coordinates">
              Coordenadas
            </ToggleButton>
            <ToggleButton value="address">
              Dirección
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>
      )}

      {/* Address Input Mode */}
      {mode === 'address' && allowAddressInput && (
        <Box sx={{ mb: 2 }}>
          <TextField
            label="Dirección"
            placeholder="Ej: Avenida Libertador Bernardo O'Higgins 1234, Santiago"
            value={addressInput}
            onChange={(e) => handleAddressInputChange(e.target.value)}
            error={error || !!geocodeError}
            helperText={error ? helperText : 'Ingrese la dirección completa y haga clic en "Buscar ubicación"'}
            fullWidth
            multiline
            rows={2}
            disabled={isGeocoding}
          />

          <Button
            variant="contained"
            startIcon={isGeocoding ? <CircularProgress size={20} /> : <SearchIcon />}
            onClick={handleGeocodeSearch}
            disabled={isGeocoding || !addressInput}
            fullWidth
            sx={{ mt: 1 }}
          >
            {isGeocoding ? 'Buscando...' : 'Buscar ubicación'}
          </Button>

          {/* Error message */}
          {geocodeError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {geocodeError}
            </Alert>
          )}

          {/* Geocoding result with map */}
          {showMap && geocodeResult && tempLocation && (
            <Box sx={{ mt: 2 }}>
              <Alert severity="info" sx={{ mb: 2 }}>
                <Typography variant="body2" sx={{ fontWeight: 'bold', mb: 1 }}>
                  Ubicación encontrada:
                </Typography>
                <Typography variant="body2">
                  {geocodeResult.formatted_address}
                </Typography>
                <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 1 }}>
                  Lat: {tempLocation[0].toFixed(6)}, Lng: {tempLocation[1].toFixed(6)}
                </Typography>
                {geocodeResult.confidence && (
                  <Typography variant="caption" color="text.secondary" display="block">
                    Confianza: {(geocodeResult.confidence * 100).toFixed(0)}%
                  </Typography>
                )}
              </Alert>

              <Box sx={{ height: 400, border: '1px solid #ccc', borderRadius: 1, mb: 2 }}>
                <MapContainer
                  center={tempLocation}
                  zoom={15}
                  style={{ height: '100%', width: '100%' }}
                  key={`${tempLocation[0]}-${tempLocation[1]}`}
                >
                  <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                  />
                  <MapRecenter center={tempLocation} />
                  <DraggableMarker position={tempLocation} onDragEnd={handleMarkerDrag} />
                </MapContainer>
              </Box>

              <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
                Puedes arrastrar el marcador para ajustar la ubicación exacta
              </Typography>

              <Button
                variant="contained"
                color="success"
                startIcon={<CheckIcon />}
                onClick={handleConfirmLocation}
                fullWidth
              >
                Confirmar ubicación
              </Button>
            </Box>
          )}
        </Box>
      )}

      {/* Coordinates Input Mode */}
      {mode === 'coordinates' && (
        <>
          <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
            <TextField
              label="Latitud"
              value={latitude}
              onChange={(e) => handleLatitudeChange(e.target.value)}
              type="number"
              inputProps={{ step: 'any', min: -90, max: 90 }}
              error={error}
              helperText={error && helperText}
              fullWidth
            />
            <TextField
              label="Longitud"
              value={longitude}
              onChange={(e) => handleLongitudeChange(e.target.value)}
              type="number"
              inputProps={{ step: 'any', min: -180, max: 180 }}
              error={error}
              fullWidth
            />
          </Box>
          <Box sx={{ height: 300, border: '1px solid #ccc', borderRadius: 1 }}>
            <MapContainer
              center={center}
              zoom={13}
              style={{ height: '100%', width: '100%' }}
              key={`${center[0]}-${center[1]}`}
            >
              <TileLayer
                attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
                url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
              />
              <MapClickHandler onClick={handleMapClick} />
              {value && <Marker position={[value.latitude, value.longitude]} />}
            </MapContainer>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
            Haz clic en el mapa para seleccionar una ubicación o ingresa las coordenadas manualmente.
          </Typography>
        </>
      )}
    </Box>
  )
}
