# Requerimientos Funcionales Detallados
## Sistema de Optimización de Rutas para Hospitalización Domiciliaria (FlamenGO!)

**Versión:** 1.0
**Fecha:** 2025-11-14
**Basado en:** Documento de Requerimientos de Alto Nivel FlamenGO!

---

## Tabla de Contenidos

1. [Introducción](#1-introducción)
2. [Backend y API](#2-backend-y-api)
3. [Motor de Optimización](#3-motor-de-optimización)
4. [Panel de Administración Web](#4-panel-de-administración-web)
5. [Aplicación Móvil](#5-aplicación-móvil)
6. [Requerimientos Transversales](#6-requerimientos-transversales)

---

## 1. Introducción

### 1.1 Propósito del Documento

Este documento especifica los requerimientos funcionales detallados del Sistema de Optimización de Rutas para Hospitalización Domiciliaria (FlamenGO!), expandiendo los requerimientos de alto nivel definidos en el documento base.

### 1.2 Alcance

El sistema consta de tres componentes principales:
- **Backend Central**: API RESTful y motor de optimización
- **Panel de Administración**: Aplicación web React.js
- **Aplicación Móvil**: App híbrida React Native (perfiles Equipo Clínico y Paciente)

### 1.3 Definiciones y Acrónimos

- **HD**: Hospitalización Domiciliaria
- **RF**: Requerimiento Funcional
- **CRUD**: Create, Read, Update, Delete
- **ETA**: Estimated Time of Arrival (Hora Estimada de Llegada)
- **GPS**: Global Positioning System
- **API**: Application Programming Interface
- **REST**: Representational State Transfer

---

## 2. Backend y API

### 2.1 Autenticación y Autorización

#### RF-BE-001: Sistema de Autenticación
**Descripción:** El sistema debe implementar un mecanismo de autenticación seguro basado en tokens JWT.

**Criterios de Aceptación:**
- El sistema debe permitir login con email/username y contraseña
- Debe generar tokens JWT con expiración configurable (por defecto 24 horas)
- Debe incluir endpoint de refresh token para renovar sesiones
- Debe implementar logout que invalide el token actual
- Las contraseñas deben almacenarse hasheadas (bcrypt o argon2)

**Validaciones:**
- Email debe tener formato válido
- Contraseña debe tener mínimo 8 caracteres
- Máximo 5 intentos fallidos antes de bloqueo temporal (15 minutos)

**Endpoints:**
- `POST /api/v1/auth/login`
- `POST /api/v1/auth/logout`
- `POST /api/v1/auth/refresh`
- `POST /api/v1/auth/change-password`

#### RF-BE-002: Gestión de Roles y Permisos
**Descripción:** El sistema debe soportar tres roles principales con permisos diferenciados.

**Roles:**
1. **Administrador**: Acceso completo al panel de administración
2. **Equipo Clínico**: Acceso a la app móvil (perfil equipo)
3. **Paciente**: Acceso a la app móvil (perfil paciente)

**Criterios de Aceptación:**
- Cada usuario debe tener asignado un rol único
- Los permisos deben validarse en cada request al backend
- Debe retornar error 403 (Forbidden) si el usuario no tiene permisos

### 2.2 Gestión de Entidades - Personal

#### RF-BE-003: CRUD de Personal
**Descripción:** El sistema debe permitir la gestión completa de los registros de personal clínico.

**Campos Obligatorios:**
- `id`: UUID generado automáticamente
- `nombre_completo`: String (max 200 caracteres)
- `email`: String, único en el sistema
- `rol_profesional`: Enum [medico, kinesiologo, tens, enfermera, otro]
- `activo`: Boolean (true por defecto)
- `created_at`: Timestamp automático
- `updated_at`: Timestamp automático

**Campos Opcionales:**
- `telefono`: String (formato validado)
- `rut`: String (validación dígito verificador)
- `especialidad`: String
- `horario_inicio`: Time (formato HH:MM)
- `horario_fin`: Time (formato HH:MM)
- `ubicacion_inicio_lat`: Decimal (latitud)
- `ubicacion_inicio_lng`: Decimal (longitud)
- `habilidades_especiales`: Array de strings

**Criterios de Aceptación:**
- Debe validar que el email sea único antes de crear
- Debe permitir soft-delete (marcar como inactivo)
- Debe mantener historial de cambios (auditoría)
- Debe validar formato de RUT chileno si es proporcionado
- Debe validar rangos de coordenadas GPS (-90 a 90 lat, -180 a 180 lng)

**Validaciones de Negocio:**
- No se puede eliminar personal que esté asignado a una ruta activa
- El horario_fin debe ser posterior al horario_inicio
- El email debe ser verificado antes de activar la cuenta

**Endpoints:**
- `GET /api/v1/personal` - Listar con paginación y filtros
- `GET /api/v1/personal/{id}` - Obtener detalle
- `POST /api/v1/personal` - Crear nuevo
- `PUT /api/v1/personal/{id}` - Actualizar
- `DELETE /api/v1/personal/{id}` - Eliminar (soft-delete)
- `GET /api/v1/personal/disponibles` - Obtener personal disponible para fecha específica

#### RF-BE-004: Disponibilidad de Personal
**Descripción:** El sistema debe permitir registrar y consultar la disponibilidad del personal por fecha.

**Criterios de Aceptación:**
- Debe permitir marcar personal como "no disponible" para fechas específicas
- Debe permitir registrar vacaciones, licencias médicas, días libres
- Debe consultar disponibilidad para una fecha específica
- Debe considerar disponibilidad en el proceso de optimización

**Campos:**
- `personal_id`: FK a Personal
- `fecha`: Date
- `disponible`: Boolean
- `motivo`: Enum [vacaciones, licencia_medica, dia_libre, capacitacion, otro]
- `notas`: Text opcional

**Endpoints:**
- `POST /api/v1/personal/{id}/disponibilidad`
- `GET /api/v1/personal/{id}/disponibilidad?fecha_inicio=YYYY-MM-DD&fecha_fin=YYYY-MM-DD`

### 2.3 Gestión de Entidades - Móviles (Vehículos)

#### RF-BE-005: CRUD de Móviles
**Descripción:** El sistema debe permitir la gestión de vehículos/ambulancias.

**Campos Obligatorios:**
- `id`: UUID
- `identificador`: String único (ej: "AMB-001", "MOV-010")
- `tipo`: Enum [ambulancia, vehiculo_medico, vehiculo_personal]
- `capacidad_personas`: Integer (1-10)
- `activo`: Boolean
- `base_lat`: Decimal (coordenada base/garaje)
- `base_lng`: Decimal (coordenada base/garaje)

**Campos Opcionales:**
- `patente`: String (formato validado chileno)
- `marca`: String
- `modelo`: String
- `año`: Integer
- `recursos_especiales`: Array de strings (ej: ["equipo_curacion", "oxigeno", "camilla"])
- `kilometraje_actual`: Integer
- `fecha_revision_tecnica`: Date
- `fecha_ultimo_mantenimiento`: Date

**Criterios de Aceptación:**
- El identificador debe ser único
- Debe validar formato de patente chilena si se proporciona
- Debe permitir soft-delete
- Debe alertar si la revisión técnica está próxima a vencer (30 días)

**Validaciones:**
- No se puede eliminar un móvil asignado a una ruta activa
- La capacidad debe ser mayor a 0
- Las coordenadas base deben estar en rango válido

**Endpoints:**
- `GET /api/v1/moviles`
- `GET /api/v1/moviles/{id}`
- `POST /api/v1/moviles`
- `PUT /api/v1/moviles/{id}`
- `DELETE /api/v1/moviles/{id}`
- `GET /api/v1/moviles/disponibles?fecha=YYYY-MM-DD`

#### RF-BE-006: Tracking de Ubicación de Móviles
**Descripción:** El sistema debe registrar y almacenar la ubicación en tiempo real de los móviles en ruta.

**Criterios de Aceptación:**
- Debe recibir actualizaciones de ubicación desde la app móvil
- Debe almacenar timestamps precisos de cada actualización
- Debe mantener las últimas 24 horas de histórico de ubicaciones
- Debe permitir consultar la última ubicación conocida de un móvil
- Debe soportar múltiples actualizaciones por minuto

**Campos:**
- `movil_id`: FK a Móviles
- `ruta_id`: FK a Rutas (opcional)
- `latitud`: Decimal
- `longitud`: Decimal
- `timestamp`: Timestamp con milisegundos
- `accuracy`: Float (precisión en metros)
- `velocidad`: Float (km/h, opcional)
- `rumbo`: Float (0-360 grados, opcional)

**Endpoints:**
- `POST /api/v1/moviles/{id}/ubicacion` - Registrar ubicación
- `GET /api/v1/moviles/{id}/ubicacion/actual` - Última ubicación
- `GET /api/v1/moviles/{id}/ubicacion/historial?desde=timestamp&hasta=timestamp`

### 2.4 Gestión de Entidades - Pacientes y Casos

#### RF-BE-007: CRUD de Pacientes
**Descripción:** El sistema debe gestionar la información de pacientes que reciben atención domiciliaria.

**Campos Obligatorios:**
- `id`: UUID
- `nombre_completo`: String
- `email`: String (único, nullable)
- `telefono`: String
- `direccion`: Text
- `latitud`: Decimal
- `longitud`: Decimal
- `activo`: Boolean

**Campos Opcionales:**
- `rut`: String (validado)
- `fecha_nacimiento`: Date
- `edad`: Integer (calculado)
- `genero`: Enum [masculino, femenino, otro, prefiero_no_decir]
- `telefono_contacto_emergencia`: String
- `nombre_contacto_emergencia`: String
- `notas_medicas`: Text
- `alergias`: Text
- `condiciones_previas`: Text
- `codigo_ficha_clinica`: String (para futura integración)

**Criterios de Aceptación:**
- Las coordenadas GPS son obligatorias para el funcionamiento del sistema
- Debe validar que las coordenadas correspondan a un área geográfica válida
- El email debe ser único si se proporciona (para acceso a app móvil)
- Debe permitir soft-delete
- Debe encriptar datos sensibles (datos médicos)

**Validaciones:**
- Formato de RUT chileno
- Formato de email válido
- Teléfono con formato internacional (+56...)
- Edad no puede ser negativa ni mayor a 120

**Endpoints:**
- `GET /api/v1/pacientes`
- `GET /api/v1/pacientes/{id}`
- `POST /api/v1/pacientes`
- `PUT /api/v1/pacientes/{id}`
- `DELETE /api/v1/pacientes/{id}`
- `POST /api/v1/pacientes/{id}/geocodificar` - Re-geocodificar dirección

#### RF-BE-008: CRUD de Casos (Visitas Programadas)
**Descripción:** Un caso representa una visita programada a un paciente para un día específico.

**Campos Obligatorios:**
- `id`: UUID
- `paciente_id`: FK a Pacientes
- `fecha_programada`: Date
- `tipo_atencion`: Enum [control_medico, curacion, kinesiologia, toma_examenes, entrega_medicamentos, otro]
- `estado`: Enum [programada, en_ruta, en_atencion, completada, cancelada]
- `prioridad`: Enum [baja, media, alta, urgente]

**Campos Opcionales:**
- `hora_inicio_ventana`: Time (ej: 09:00)
- `hora_fin_ventana`: Time (ej: 12:00)
- `duracion_estimada`: Integer (minutos)
- `requiere_roles`: Array de Enum [medico, kinesiologo, tens, enfermera]
- `requiere_recursos`: Array de strings (ej: ["equipo_curacion", "toma_presion"])
- `notas`: Text
- `ruta_id`: FK a Rutas (se asigna al optimizar)
- `orden_en_ruta`: Integer (se asigna al optimizar)
- `hora_inicio_real`: Timestamp (se registra al iniciar)
- `hora_fin_real`: Timestamp (se registra al completar)

**Criterios de Aceptación:**
- Un paciente puede tener múltiples casos en diferentes fechas
- Si se especifica ventana de tiempo, hora_fin debe ser posterior a hora_inicio
- La duración estimada por defecto es 30 minutos
- El estado inicial debe ser "programada"
- Si no se especifican roles requeridos, se asume [medico, tens]

**Validaciones de Negocio:**
- No se pueden crear casos para fechas pasadas
- La ventana de tiempo debe estar dentro del horario laboral (07:00 - 20:00)
- No se puede cambiar estado a "completada" sin registrar hora_fin_real
- No se puede eliminar un caso que esté en estado "en_atencion"

**Endpoints:**
- `GET /api/v1/casos?fecha=YYYY-MM-DD&estado=programada`
- `GET /api/v1/casos/{id}`
- `POST /api/v1/casos`
- `PUT /api/v1/casos/{id}`
- `DELETE /api/v1/casos/{id}`
- `PATCH /api/v1/casos/{id}/estado` - Cambiar estado específicamente
- `GET /api/v1/casos/sin-asignar?fecha=YYYY-MM-DD` - Casos sin ruta asignada

### 2.5 Gestión de Matriz de Distancias

#### RF-BE-009: Cálculo de Distancias y Tiempos
**Descripción:** El sistema debe calcular distancias y tiempos de viaje entre ubicaciones usando servicios de mapas externos.

**Criterios de Aceptación:**
- Debe integrar con al menos un servicio de mapas (Google Maps API, OSRM, MapBox)
- Debe calcular distancia en kilómetros y tiempo en minutos
- Debe considerar tráfico actual si está disponible
- Debe cachear resultados para reducir costos de API
- El cache debe tener TTL configurable (por defecto 1 hora)

**Entrada:**
- Origen: latitud, longitud
- Destino: latitud, longitud
- Timestamp: para considerar tráfico en hora específica (opcional)

**Salida:**
- `distancia_km`: Float
- `tiempo_minutos`: Integer
- `ruta_polilinea`: String (encoded polyline, opcional)

**Endpoints:**
- `POST /api/v1/geoservicios/calcular-distancia`
- `POST /api/v1/geoservicios/matriz-distancias` - Cálculo masivo origen-múltiples destinos

**Validaciones:**
- Coordenadas deben estar en rangos válidos
- Debe manejar errores del servicio externo gracefully
- Debe tener mecanismo de fallback si el servicio externo falla

#### RF-BE-010: Geocodificación de Direcciones
**Descripción:** El sistema debe convertir direcciones de texto a coordenadas GPS.

**Criterios de Aceptación:**
- Debe permitir geocodificar direcciones chilenas
- Debe retornar latitud, longitud y dirección formateada
- Debe validar que la dirección sea encontrada
- Debe permitir selección manual si hay múltiples resultados

**Entrada:**
- `direccion`: String
- `ciudad`: String (opcional, ayuda a precisión)
- `region`: String (opcional)

**Salida:**
- `latitud`: Decimal
- `longitud`: Decimal
- `direccion_formateada`: String
- `precision`: Enum [exacta, aproximada, calle, ciudad]

**Endpoints:**
- `POST /api/v1/geoservicios/geocodificar`

---

## 3. Motor de Optimización

### 3.1 Proceso de Optimización

#### RF-OPT-001: Planificación de Rutas Óptimas
**Descripción:** El motor debe generar rutas óptimas asignando casos a móviles y ordenándolos eficientemente.

**Entrada (Request):**
```json
{
  "fecha": "2025-11-15",
  "casos_ids": ["uuid1", "uuid2", "uuid3", ...],
  "personal_ids": ["uuid_personal1", "uuid_personal2", ...],
  "moviles_ids": ["uuid_movil1", "uuid_movil2", ...],
  "opciones": {
    "objetivo": "minimizar_tiempo_total|minimizar_distancia|balance",
    "permitir_violacion_ventanas": false,
    "tiempo_max_optimizacion_seg": 30
  }
}
```

**Salida (Response):**
```json
{
  "rutas": [
    {
      "ruta_id": "uuid_ruta",
      "movil_id": "uuid",
      "personal_asignado": ["uuid_personal1", "uuid_personal2"],
      "casos": [
        {
          "caso_id": "uuid",
          "orden": 1,
          "hora_llegada_estimada": "09:30",
          "hora_salida_estimada": "10:00"
        }
      ],
      "metricas": {
        "distancia_total_km": 45.2,
        "tiempo_total_minutos": 320,
        "tiempo_viaje_minutos": 140,
        "tiempo_atencion_minutos": 180
      }
    }
  ],
  "casos_no_asignados": ["uuid_caso_x"],
  "warnings": ["Personal insuficiente para cubrir todos los casos"],
  "tiempo_calculo_seg": 12.4
}
```

**Criterios de Aceptación:**
- Debe respetar las ventanas de tiempo de los casos (si están definidas)
- Debe asignar personal con las habilidades requeridas por cada caso
- Debe respetar la capacidad de cada móvil
- Debe considerar la ubicación inicial de cada móvil (base)
- Debe optimizar según el objetivo especificado
- Debe completar el cálculo en el tiempo máximo especificado
- Si no puede asignar todos los casos, debe retornar los no asignados

**Restricciones Duras (No Violables):**
1. Un móvil no puede estar en dos lugares al mismo tiempo
2. El personal asignado debe tener las habilidades requeridas
3. No se puede exceder la capacidad del móvil
4. El personal asignado debe estar disponible en la fecha

**Restricciones Blandas (Penalizables):**
1. Preferir cumplir ventanas de tiempo
2. Preferir minimizar tiempo de viaje
3. Preferir balancear carga entre móviles

**Validaciones:**
- Todos los IDs deben existir en el sistema
- La fecha no puede ser pasada
- Debe haber al menos 1 caso, 1 móvil y personal suficiente
- Los casos deben estar en estado "programada"

**Endpoints:**
- `POST /api/v1/optimizacion/calcular-rutas`

#### RF-OPT-002: Algoritmo de Optimización
**Descripción:** El sistema debe implementar un algoritmo robusto de optimización de rutas.

**Enfoque Técnico Sugerido:**
- Algoritmo genético, Simulated Annealing, o VRP Solver (OR-Tools)
- Modelado como Vehicle Routing Problem with Time Windows (VRPTW)
- Considerar restricciones múltiples (capacidad, habilidades, ventanas)

**Criterios de Aceptación:**
- Debe escalar para al menos 50 casos, 10 móviles, 20 personal
- Debe encontrar solución factible en menos de 30 segundos
- Debe priorizar casos de alta urgencia
- Debe poder ejecutarse de forma asíncrona para grandes volúmenes

**Métricas de Calidad:**
- Porcentaje de casos asignados (objetivo: >95%)
- Desviación de ventanas de tiempo (objetivo: <5%)
- Balance de carga entre móviles (desviación estándar <20%)

#### RF-OPT-003: Re-optimización Dinámica
**Descripción:** El sistema debe permitir re-calcular rutas cuando ocurren cambios durante el día.

**Casos de Uso:**
- Caso cancelado durante ejecución
- Caso urgente agregado
- Móvil fuera de servicio
- Retraso significativo en un móvil

**Criterios de Aceptación:**
- Debe poder recalcular solo las rutas afectadas
- Debe mantener las visitas ya completadas
- Debe minimizar cambios en las rutas existentes
- Debe notificar a equipos y pacientes afectados

**Endpoints:**
- `POST /api/v1/optimizacion/re-calcular`
- `POST /api/v1/rutas/{id}/recalcular-desde-actual`

### 3.2 Gestión de Rutas Generadas

#### RF-OPT-004: CRUD de Rutas
**Descripción:** El sistema debe almacenar y gestionar las rutas generadas por el motor de optimización.

**Campos:**
- `id`: UUID
- `fecha`: Date
- `movil_id`: FK
- `estado`: Enum [planificada, activa, pausada, completada, cancelada]
- `personal_asignado`: Array de UUIDs
- `hora_inicio_planificada`: Time
- `hora_fin_planificada`: Time
- `hora_inicio_real`: Timestamp
- `hora_fin_real`: Timestamp
- `distancia_total_km`: Float (planificada)
- `distancia_recorrida_km`: Float (real)
- `casos_asignados`: Relación con Casos
- `notas`: Text

**Criterios de Aceptación:**
- Una ruta debe asociarse a exactamente un móvil
- Una ruta puede tener múltiples casos ordenados
- El estado inicial es "planificada"
- Al iniciar la ruta (desde app móvil), cambia a "activa"

**Endpoints:**
- `GET /api/v1/rutas?fecha=YYYY-MM-DD&estado=activa`
- `GET /api/v1/rutas/{id}`
- `PATCH /api/v1/rutas/{id}/estado`
- `DELETE /api/v1/rutas/{id}` - Solo si está en estado planificada

#### RF-OPT-005: Consulta de Rutas por Móvil
**Descripción:** La app móvil debe poder consultar la ruta asignada a un móvil específico.

**Criterios de Aceptación:**
- Debe retornar la ruta activa del día para el móvil autenticado
- Debe incluir lista ordenada de casos con datos del paciente
- Debe incluir coordenadas para navegación
- Debe indicar el estado actual de cada caso en la ruta

**Response Ejemplo:**
```json
{
  "ruta_id": "uuid",
  "fecha": "2025-11-15",
  "estado": "activa",
  "personal_asignado": [
    {"id": "uuid", "nombre": "Dr. Juan Pérez", "rol": "medico"}
  ],
  "casos": [
    {
      "caso_id": "uuid",
      "orden": 1,
      "paciente": {
        "nombre": "María González",
        "direccion": "Av. Principal 123",
        "telefono": "+56912345678",
        "latitud": -33.4569,
        "longitud": -70.6483
      },
      "tipo_atencion": "control_medico",
      "duracion_estimada": 30,
      "hora_llegada_estimada": "09:30",
      "estado": "programada",
      "notas": "Paciente con movilidad reducida"
    }
  ]
}
```

**Endpoints:**
- `GET /api/v1/moviles/{id}/ruta-del-dia?fecha=YYYY-MM-DD`
- `GET /api/v1/rutas/mi-ruta` - Para usuario autenticado (equipo clínico)

---

## 4. Panel de Administración Web

### 4.1 Dashboard Principal

#### RF-WEB-001: Dashboard de Monitoreo
**Descripción:** El panel debe mostrar una vista general del estado del sistema.

**Componentes del Dashboard:**

1. **Resumen del Día:**
   - Total de casos programados
   - Casos completados / en progreso / pendientes
   - Móviles activos / inactivos
   - Personal disponible

2. **Mapa en Tiempo Real:**
   - Ubicación actual de todos los móviles activos
   - Iconos diferenciados por estado (en ruta, en atención, regresando)
   - Al hacer clic en un móvil, mostrar:
     - Identificador del móvil
     - Personal asignado
     - Caso actual o siguiente caso
     - ETA al siguiente destino

3. **Alertas y Notificaciones:**
   - Retrasos significativos (>15 minutos)
   - Casos urgentes sin asignar
   - Móviles sin reportar ubicación (>10 minutos)
   - Revisiones técnicas próximas a vencer

**Criterios de Aceptación:**
- El mapa debe actualizarse automáticamente cada 30 segundos
- Las métricas deben ser precisas y actualizarse en tiempo real
- Debe permitir filtrar por fecha
- Debe ser responsive (funcionar en tablets)

#### RF-WEB-002: Selección de Vista de Fecha
**Descripción:** El usuario debe poder seleccionar una fecha para visualizar o planificar.

**Criterios de Aceptación:**
- Debe tener un selector de fecha prominente
- Por defecto debe mostrar la fecha actual
- Debe permitir seleccionar fechas futuras para planificación
- Debe permitir ver fechas pasadas para historial
- Al cambiar fecha, debe actualizar todas las vistas

### 4.2 Gestión de Recursos

#### RF-WEB-003: Módulo de Gestión de Personal
**Descripción:** Interfaz CRUD para gestionar el personal clínico.

**Funcionalidades:**

1. **Lista de Personal:**
   - Tabla con columnas: Nombre, Rol, Email, Teléfono, Estado
   - Filtros: por rol, por estado (activo/inactivo)
   - Búsqueda por nombre o email
   - Paginación (20 registros por página)
   - Botón "Agregar Personal"

2. **Formulario de Creación/Edición:**
   - Campos según RF-BE-003
   - Validación en frontend antes de enviar
   - Mensajes de error claros
   - Selector de ubicación en mapa para ubicación_inicio
   - Selector múltiple para habilidades especiales

3. **Vista de Detalle:**
   - Mostrar toda la información del personal
   - Historial de rutas asignadas (últimas 10)
   - Botón "Editar" y "Desactivar"
   - Calendario de disponibilidad

**Criterios de Aceptación:**
- Debe validar todos los campos antes de enviar
- Debe mostrar confirmación antes de desactivar personal
- Debe mostrar mensaje de éxito/error después de cada operación
- El selector de ubicación en mapa debe ser intuitivo

#### RF-WEB-004: Módulo de Gestión de Móviles
**Descripción:** Interfaz CRUD para gestionar vehículos/ambulancias.

**Funcionalidades:**
- Lista con tabla similar a Personal
- Formulario con campos según RF-BE-005
- Selector de ubicación base en mapa
- Selector múltiple para recursos especiales
- Indicador visual de alertas (ej: revisión técnica próxima)

**Criterios de Aceptación:**
- Similar a RF-WEB-003
- Debe resaltar visualmente móviles con alertas
- Debe mostrar estado actual (disponible, en ruta, mantenimiento)

#### RF-WEB-005: Módulo de Gestión de Pacientes
**Descripción:** Interfaz CRUD para gestionar pacientes.

**Funcionalidades:**
- Lista con búsqueda avanzada (por nombre, RUT, dirección)
- Formulario de creación/edición con campos según RF-BE-007
- Integración con servicio de geocodificación
- Vista de mapa para confirmar ubicación
- Opción de "Re-geocodificar" si la dirección cambió

**Funcionalidad Especial - Geocodificación:**
- Al ingresar/editar dirección, botón "Geocodificar"
- Mostrar mapa con pin en la ubicación encontrada
- Permitir ajustar manualmente el pin si es necesario
- Guardar coordenadas ajustadas

**Criterios de Aceptación:**
- La geocodificación debe ser obligatoria antes de guardar
- Debe validar que las coordenadas estén en Chile
- Debe proteger datos médicos sensibles (solo visible para admins)

#### RF-WEB-006: Módulo de Gestión de Casos
**Descripción:** Interfaz para crear y gestionar visitas programadas.

**Funcionalidades:**

1. **Vista de Calendario:**
   - Calendario mensual con indicadores de casos por día
   - Al hacer clic en un día, mostrar lista de casos
   - Botón "Agregar Caso" con selector de fecha

2. **Lista de Casos (por fecha):**
   - Tabla: Paciente, Tipo Atención, Ventana Horaria, Estado, Asignado a
   - Filtros: por estado, por tipo de atención, por prioridad
   - Indicador visual de prioridad (colores)
   - Ordenamiento por hora de ventana

3. **Formulario de Caso:**
   - Selector de paciente (con búsqueda)
   - Fecha programada (date picker)
   - Tipo de atención (dropdown)
   - Prioridad (selector visual)
   - Ventana horaria opcional (time pickers)
   - Duración estimada (input numérico, minutos)
   - Selector múltiple de roles requeridos
   - Selector múltiple de recursos requeridos
   - Área de notas (textarea)

**Criterios de Aceptación:**
- Debe validar que la fecha no sea pasada
- Debe validar ventana horaria (fin > inicio)
- Debe mostrar dirección y ubicación del paciente al seleccionarlo
- Debe permitir edición solo si el caso no está "completada"
- Debe pedir confirmación antes de cancelar un caso en ruta

### 4.3 Planificación de Jornada

#### RF-WEB-007: Interfaz de Planificación Diaria
**Descripción:** Interfaz principal para preparar y ejecutar la optimización de rutas.

**Vista Principal - Tres Paneles:**

1. **Panel Izquierdo: Casos del Día**
   - Lista de casos programados para la fecha seleccionada
   - Agrupados por estado:
     - Sin asignar (checkbox selectable)
     - Ya asignados a ruta
   - Checkbox para seleccionar múltiples
   - Botón "Seleccionar Todos Sin Asignar"
   - Filtros: prioridad, tipo atención, zona geográfica

2. **Panel Central: Recursos Disponibles**
   - Lista de móviles disponibles (checkbox)
   - Para cada móvil, mostrar:
     - Personal disponible para asignar (multiselect)
     - Capacidad
     - Recursos especiales
   - Resumen: X móviles, Y personal seleccionado

3. **Panel Derecho: Opciones de Optimización**
   - Selector de objetivo:
     - Minimizar tiempo total
     - Minimizar distancia
     - Balance entre tiempo y distancia
   - Checkbox: "Permitir violación de ventanas de tiempo"
   - Tiempo máximo de cálculo (slider, 10-60 seg)
   - Botón grande: "CALCULAR RUTAS ÓPTIMAS"

**Criterios de Aceptación:**
- Debe validar que haya al menos 1 caso, 1 móvil, y personal seleccionado
- Debe mostrar resumen de selección antes de calcular
- Debe deshabilitar el botón mientras está calculando
- Debe mostrar indicador de progreso durante cálculo

#### RF-WEB-008: Visualización de Rutas Generadas
**Descripción:** Después de la optimización, mostrar las rutas generadas para revisión y aprobación.

**Vista de Resultados:**

1. **Resumen General:**
   - Casos asignados: X de Y
   - Distancia total: X km
   - Tiempo total estimado: X horas
   - Casos no asignados (si los hay)

2. **Lista de Rutas (Acordeón):**
   - Una sección colapsable por cada móvil
   - Header de cada ruta:
     - Identificador del móvil
     - Personal asignado
     - Nº de casos
     - Distancia total
     - Tiempo total
   - Contenido expandible:
     - Lista ordenada de casos con:
       - Orden
       - Paciente
       - Dirección
       - Hora estimada de llegada
       - Hora estimada de salida
     - Botones: "Ver en Mapa", "Editar Orden"

3. **Mapa de Todas las Rutas:**
   - Mostrar todas las rutas en diferentes colores
   - Pins numerados para cada visita
   - Líneas conectoras mostrando el recorrido
   - Selector para mostrar/ocultar rutas individuales

4. **Acciones:**
   - Botón "CONFIRMAR Y ACTIVAR RUTAS"
   - Botón "RE-CALCULAR" (con opciones diferentes)
   - Botón "CANCELAR"

**Criterios de Aceptación:**
- Debe permitir revisar cada ruta en detalle
- Debe permitir editar manualmente el orden de casos (drag & drop)
- Debe recalcular tiempos si se modifica el orden
- Al confirmar, debe cambiar el estado de rutas a "planificada"
- Debe notificar automáticamente a los equipos móviles

#### RF-WEB-009: Ajustes Manuales de Rutas
**Descripción:** Permitir al administrador hacer ajustes manuales a las rutas generadas.

**Funcionalidades:**
- Cambiar orden de casos en una ruta (drag & drop)
- Mover un caso de una ruta a otra
- Re-asignar personal a una ruta
- Agregar o quitar casos de una ruta

**Criterios de Aceptación:**
- Debe validar restricciones (capacidad, habilidades)
- Debe recalcular métricas automáticamente tras cada cambio
- Debe mostrar warnings si se violan restricciones
- Debe permitir "deshacer" cambios antes de confirmar

### 4.4 Monitoreo en Tiempo Real

#### RF-WEB-010: Vista de Rutas Activas
**Descripción:** Monitorear el progreso de las rutas durante su ejecución.

**Componentes:**

1. **Lista de Rutas Activas:**
   - Tarjetas para cada móvil en ruta
   - Por cada tarjeta mostrar:
     - Identificador y personal
     - Caso actual (o "En camino a...")
     - Progreso: X de Y casos completados
     - ETA al siguiente caso
     - Indicador de estado (verde: a tiempo, amarillo: leve retraso, rojo: retraso significativo)

2. **Mapa en Tiempo Real:**
   - Ubicación actual de móviles (actualización cada 30 seg)
   - Ruta planificada vs. ruta real
   - Casos completados (check verde)
   - Caso actual (pin pulsante)
   - Casos pendientes (pins grises)

3. **Timeline de Eventos:**
   - Lista cronológica de eventos:
     - "Móvil X inició ruta" - HH:MM
     - "Móvil X llegó a caso Y" - HH:MM
     - "Móvil X completó caso Y" - HH:MM
     - "Móvil X reportó retraso" - HH:MM

**Criterios de Aceptación:**
- Debe actualizarse en tiempo real (websockets o polling)
- Debe alertar visualmente retrasos >15 minutos
- Debe permitir hacer clic en un móvil para ver detalles
- Debe mostrar última actualización de ubicación

#### RF-WEB-011: Acciones en Rutas Activas
**Descripción:** Permitir intervenciones durante la ejecución de rutas.

**Acciones Disponibles:**
- Re-asignar un caso no iniciado a otro móvil
- Cancelar un caso (con confirmación)
- Agregar caso urgente a una ruta existente
- Pausar una ruta
- Marcar móvil como "Fuera de servicio"

**Criterios de Aceptación:**
- Debe solicitar confirmación para acciones críticas
- Debe notificar inmediatamente al equipo móvil afectado
- Debe recalcular rutas si es necesario
- Debe registrar todas las acciones en bitácora

---

## 5. Aplicación Móvil

### 5.1 Funcionalidades Comunes

#### RF-MOV-001: Autenticación
**Descripción:** La app debe permitir login seguro con dos perfiles.

**Criterios de Aceptación:**
- Pantalla de login con email/username y contraseña
- Opción "Recordar sesión"
- Recuperación de contraseña vía email
- Detección automática del tipo de perfil tras login
- Redirección a la interfaz correspondiente (Equipo o Paciente)

**Validaciones:**
- Máximo 5 intentos fallidos antes de bloqueo temporal
- Mensaje de error claro en caso de credenciales incorrectas

#### RF-MOV-002: Notificaciones Push
**Descripción:** La app debe recibir y mostrar notificaciones en tiempo real.

**Tipos de Notificaciones:**
- **Para Equipo Clínico:**
  - "Nueva ruta asignada para hoy"
  - "Ruta ha sido modificada"
  - "Nuevo caso urgente agregado"
  - "Caso cancelado"
- **Para Paciente:**
  - "Su visita ha sido programada para mañana"
  - "El equipo está en camino (20 min)"
  - "El equipo llegará en 5 minutos"
  - "Su visita ha sido reprogramada"

**Criterios de Aceptación:**
- Debe solicitar permisos de notificaciones al primer uso
- Debe mostrar badge con contador de notificaciones no leídas
- Debe mantener historial de notificaciones
- Debe funcionar incluso si la app está cerrada

### 5.2 Perfil: Equipo Clínico

#### RF-MOV-003: Vista de Hoja de Ruta
**Descripción:** Interfaz principal para que el equipo vea y ejecute su ruta del día.

**Pantalla Principal:**

1. **Header:**
   - Fecha actual
   - Identificador del móvil
   - Personal asignado
   - Progreso: "3 de 8 completadas"

2. **Lista de Casos (Ordenada):**
   - Para cada caso, mostrar tarjeta con:
     - Número de orden
     - Nombre del paciente
     - Dirección
     - Hora estimada
     - Tipo de atención
     - Estado actual (badge con color)
   - Estado del caso:
     - Pendiente (gris)
     - Siguiente (azul, resaltado)
     - En camino (amarillo)
     - En atención (verde)
     - Completado (verde con check)
     - Cancelado (rojo tachado)

3. **Acciones por Caso:**
   - Botón "NAVEGAR" - Abre app de mapas
   - Botón "LLAMAR" - Llama al paciente
   - Botón de cambio de estado

**Criterios de Aceptación:**
- El caso "siguiente" debe estar siempre visible (scroll automático)
- Debe mostrar distancia y tiempo estimado al siguiente caso
- Debe permitir scroll para ver todos los casos
- Debe actualizar en tiempo real si hay cambios desde el backend

#### RF-MOV-004: Navegación a Casos
**Descripción:** Integración con apps de navegación para guiar al equipo.

**Funcionalidad:**
- Al presionar "NAVEGAR", abrir selector de app:
  - Google Maps
  - Waze
  - Apple Maps (iOS)
- Pasar coordenadas y dirección de destino
- Al regresar a la app, preguntar si llegaron al destino

**Criterios de Aceptación:**
- Debe detectar qué apps de navegación están instaladas
- Debe manejar caso donde no hay apps instaladas
- Debe ser intuitivo y con un solo tap

#### RF-MOV-005: Gestión de Estados de Casos
**Descripción:** Permitir al equipo actualizar el estado de cada caso durante la jornada.

**Flujo de Estados:**
1. **Pendiente** → Botón "INICIAR VIAJE"
2. **En Camino** → Botón "HE LLEGADO"
3. **En Atención** → Botón "FINALIZAR ATENCIÓN"
4. **Completado** → (estado final)

**Opciones Adicionales:**
- "CANCELAR VISITA" - disponible en cualquier momento (con motivo)
- "REPORTAR PROBLEMA" - envía alerta a administrador

**Criterios de Aceptación:**
- Cada cambio de estado debe registrar timestamp
- Debe solicitar confirmación en acciones críticas
- Debe enviar actualización inmediata al backend
- Debe funcionar offline (guardar para sincronizar después)

**Formulario de Finalización:**
Al presionar "FINALIZAR ATENCIÓN", mostrar form:
- Duración real de la atención (pre-llenado automático)
- Checkbox: "¿Atención completada exitosamente?"
- Campo de notas (opcional)
- Firma digital (opcional, para futuras fases)
- Botón "CONFIRMAR"

#### RF-MOV-006: Reporte de Ubicación GPS
**Descripción:** La app debe enviar la ubicación del dispositivo al backend continuamente.

**Comportamiento:**
- Solicitar permisos de ubicación al iniciar sesión
- Mientras hay una ruta activa:
  - Enviar ubicación cada 30 segundos (configurable)
  - Usar servicio en background
  - Funcionar incluso si la app está minimizada
- Detener reporte al finalizar la ruta del día

**Criterios de Aceptación:**
- Debe obtener ubicación de alta precisión (GPS)
- Debe manejar gracefully si no hay señal GPS
- Debe optimizar consumo de batería
- Debe funcionar en iOS y Android

**Manejo de Errores:**
- Si no hay conexión, almacenar en cola local
- Sincronizar cuando se recupere conexión
- Alertar al usuario si no se puede obtener ubicación

#### RF-MOV-007: Vista de Detalle de Caso
**Descripción:** Al hacer tap en un caso, mostrar toda la información disponible.

**Información Mostrada:**
- Datos del paciente:
  - Nombre completo
  - Dirección completa
  - Teléfono (botón para llamar)
  - Contacto de emergencia
- Datos de la visita:
  - Tipo de atención
  - Hora ventana (si aplica)
  - Duración estimada
  - Notas especiales
  - Recursos requeridos
- Información médica (si disponible):
  - Alergias
  - Condiciones previas
  - Notas médicas

**Criterios de Aceptación:**
- Debe proteger información sensible
- Debe permitir navegación rápida entre casos (swipe)
- Debe tener acceso rápido a llamada y navegación

#### RF-MOV-008: Historial y Estadísticas
**Descripción:** Sección para que el equipo vea su historial de rutas.

**Funcionalidades:**
- Lista de rutas pasadas (últimos 30 días)
- Por cada ruta:
  - Fecha
  - Casos completados
  - Kilómetros recorridos
  - Horas trabajadas
- Estadísticas acumuladas:
  - Total de visitas realizadas
  - Promedio de visitas por día
  - Distancia total recorrida

**Criterios de Aceptación:**
- Debe cargar bajo demanda (no al abrir la app)
- Debe permitir ver detalle de cada ruta pasada
- Debe ser solo lectura

### 5.3 Perfil: Paciente

#### RF-MOV-009: Vista de Visita Programada
**Descripción:** Pantalla principal para que el paciente vea su próxima visita.

**Pantalla Principal:**

1. **Tarjeta de Visita:**
   - Título: "Tu próxima visita"
   - Fecha y hora (ventana si aplica)
   - Tipo de atención
   - Estado actual:
     - "Programada para mañana"
     - "Hoy, entre las 10:00 y 12:00"
     - "El equipo está en camino"
     - "Visita completada"

2. **Información del Equipo (cuando esté en camino):**
   - Nombre del personal que atenderá
   - Rol (médico, kinesiólogo, etc.)
   - Tiempo estimado de llegada (minutos)
   - Distancia aproximada

3. **Acciones:**
   - Botón "LLAMAR A COORDINACIÓN" (fijo)
   - Botón "CANCELAR VISITA" (con confirmación)

**Criterios de Aceptación:**
- Debe mostrar solo la próxima visita pendiente
- Debe actualizar automáticamente cuando cambia el estado
- Debe ser interfaz simple e intuitiva (para adultos mayores)

#### RF-MOV-010: Seguimiento en Mapa (Tipo Uber)
**Descripción:** Cuando el equipo está en camino, mostrar su ubicación en tiempo real.

**Funcionalidad:**
- Se activa automáticamente cuando el caso cambia a estado "En Camino"
- Mostrar mapa con:
  - Pin del paciente (domicilio)
  - Pin del móvil (ubicación actual)
  - Línea/ruta estimada entre ambos
  - ETA actualizado (ej: "Llegan en 12 minutos")

**Criterios de Aceptación:**
- El mapa debe actualizarse cada 30 segundos
- Debe mostrar solo cuando el equipo está efectivamente en camino a ese paciente
- Debe centrarse automáticamente para mostrar ambos puntos
- Debe funcionar en conexiones lentas (mapa simplificado si es necesario)

**Estados del Mapa:**
- "El equipo iniciará el viaje pronto" - mapa estático
- "El equipo está en camino" - mapa dinámico con actualización
- "El equipo está por llegar (2 min)" - alerta visual
- "El equipo ha llegado" - mensaje de confirmación

#### RF-MOV-011: Notificaciones para Paciente
**Descripción:** Sistema de alertas proactivas para mantener informado al paciente.

**Notificaciones Automáticas:**
1. **24 horas antes:** "Recordatorio: Mañana tienes visita médica entre las 10:00 y 12:00"
2. **2 horas antes:** "Tu visita está confirmada para hoy. El equipo saldrá pronto"
3. **Al iniciar viaje:** "El equipo está en camino a tu domicilio"
4. **5 minutos antes:** "El equipo llegará en 5 minutos"
5. **Al llegar:** "El equipo ha llegado a tu domicilio"
6. **Cambios:** "Tu visita ha sido reprogramada para mañana a las 14:00"

**Criterios de Aceptación:**
- Todas las notificaciones deben ser claras y en lenguaje simple
- Debe respetar horarios (no enviar entre 22:00 y 08:00)
- Debe permitir configurar preferencias de notificaciones

#### RF-MOV-012: Historial de Visitas del Paciente
**Descripción:** Sección para ver historial de atenciones recibidas.

**Funcionalidades:**
- Lista de visitas pasadas (últimos 6 meses)
- Por cada visita:
  - Fecha
  - Tipo de atención
  - Personal que atendió
  - Estado (completada, cancelada)
- Filtro por fecha

**Criterios de Aceptación:**
- Debe ser solo lectura
- Debe cargar bajo demanda
- Debe ser accesible sin conexión (cache local)

#### RF-MOV-013: Información de Contacto
**Descripción:** Sección con información de contacto del servicio.

**Información Mostrada:**
- Teléfono de coordinación
- Email de contacto
- Horario de atención
- Dirección de la institución
- Botones de acceso rápido:
  - "Llamar ahora"
  - "Enviar email"
  - "Ver en mapa"

**Criterios de Aceptación:**
- Debe estar siempre accesible desde el menú principal
- Los botones deben abrir las apps nativas correspondientes

---

## 6. Requerimientos Transversales

### 6.1 Seguridad

#### RF-SEC-001: Encriptación de Datos Sensibles
**Descripción:** Los datos sensibles deben estar encriptados en reposo y en tránsito.

**Criterios:**
- Comunicación HTTPS obligatoria (TLS 1.2+)
- Contraseñas hasheadas con bcrypt o argon2
- Datos médicos encriptados en BD
- Tokens JWT firmados y con expiración

#### RF-SEC-002: Control de Acceso
**Descripción:** Implementar control de acceso basado en roles (RBAC).

**Matriz de Permisos:**
| Recurso | Administrador | Equipo Clínico | Paciente |
|---------|---------------|----------------|----------|
| Gestionar Personal | ✓ | ✗ | ✗ |
| Gestionar Móviles | ✓ | ✗ | ✗ |
| Gestionar Pacientes | ✓ | ✗ | ✗ |
| Gestionar Casos | ✓ | ✗ | ✗ |
| Calcular Rutas | ✓ | ✗ | ✗ |
| Ver Rutas del Día | ✓ | ✓ (solo propia) | ✗ |
| Actualizar Estado Caso | ✓ | ✓ (solo asignados) | ✗ |
| Reportar Ubicación | ✗ | ✓ | ✗ |
| Ver Propia Visita | ✗ | ✗ | ✓ |
| Ver Seguimiento Mapa | ✗ | ✗ | ✓ |

#### RF-SEC-003: Auditoría
**Descripción:** Registrar todas las acciones críticas en log de auditoría.

**Eventos a Registrar:**
- Login/logout de usuarios
- Creación/modificación/eliminación de recursos
- Ejecución de optimización
- Cambios manuales en rutas
- Cambios de estado de casos
- Acceso a datos médicos sensibles

**Información del Log:**
- Timestamp
- Usuario (ID y email)
- Acción realizada
- Recurso afectado
- IP de origen
- Resultado (éxito/fallo)

### 6.2 Rendimiento

#### RF-PERF-001: Tiempos de Respuesta
**Descripción:** El sistema debe cumplir con tiempos de respuesta aceptables.

**Objetivos:**
- Endpoints CRUD: <500ms (p95)
- Optimización de rutas: <30s (casos típicos <20)
- Consulta de ubicaciones: <200ms
- Carga de mapa en tiempo real: <2s

#### RF-PERF-002: Escalabilidad
**Descripción:** El sistema debe soportar crecimiento en volumen de datos y usuarios.

**Capacidad Mínima:**
- 100 pacientes activos
- 50 casos diarios
- 10 móviles simultáneos
- 30 usuarios del panel web concurrentes
- 50 usuarios de app móvil concurrentes

**Preparación para Escala:**
- Arquitectura preparada para escalamiento horizontal
- Base de datos con índices optimizados
- Cache para consultas frecuentes

### 6.3 Disponibilidad

#### RF-DISP-001: Disponibilidad del Servicio
**Descripción:** El sistema debe estar disponible durante horarios operativos.

**Objetivo:** 99% de disponibilidad durante horario laboral (07:00 - 20:00)

**Medidas:**
- Monitoreo de salud del sistema
- Backup automático diario
- Plan de recuperación ante desastres

#### RF-DISP-002: Funcionamiento Offline (App Móvil)
**Descripción:** La app móvil debe tener capacidades básicas offline.

**Funcionalidades Offline:**
- Ver la ruta del día (cacheada)
- Ver detalles de casos
- Cambiar estados de casos (sincroniza después)
- Ver mapa estático de ubicaciones

**Sincronización:**
- Automática al recuperar conexión
- Manual mediante botón "Sincronizar"
- Indicador visual de "Datos pendientes de sincronizar"

### 6.4 Usabilidad

#### RF-USA-001: Accesibilidad
**Descripción:** Las interfaces deben ser accesibles y fáciles de usar.

**Criterios:**
- Textos con contraste suficiente (WCAG AA)
- Tamaño de fuente ajustable
- Botones con área de tap >44px (móvil)
- Mensajes de error claros y accionables
- Diseño responsive

#### RF-USA-002: Internacionalización
**Descripción:** El sistema debe soportar idioma español (chileno).

**Consideraciones:**
- Formatos de fecha: DD/MM/YYYY
- Formatos de hora: 24 horas (HH:MM)
- Moneda: CLP (para futuros módulos de costos)
- Validaciones locales: RUT chileno, patentes, etc.

### 6.5 Integración Futura

#### RF-INT-001: Preparación para Integración con Ficha Clínica
**Descripción:** La arquitectura debe facilitar futura integración con sistemas de ficha clínica.

**Preparación:**
- Campo `codigo_ficha_clinica` en entidad Paciente
- Campos de timestamps para sincronización
- API diseñada para exponer endpoints de integración
- Documentación de API con OpenAPI/Swagger

#### RF-INT-002: Webhooks
**Descripción:** El sistema debe permitir notificar eventos a sistemas externos.

**Eventos Publicables:**
- Ruta creada
- Caso completado
- Caso cancelado
- Móvil fuera de servicio

**Formato:**
- HTTP POST a URL configurada
- Payload JSON con datos del evento
- Reintentos con backoff exponencial

---

## Resumen de Prioridades

### Fase 1 - MVP (Mínimo Viable)
- RF-BE-001 a RF-BE-008 (Backend core + Entidades)
- RF-BE-009 (Cálculo distancias)
- RF-OPT-001, RF-OPT-004 (Optimización básica)
- RF-WEB-003 a RF-WEB-006 (Gestión de recursos)
- RF-WEB-007, RF-WEB-008 (Planificación)
- RF-MOV-001, RF-MOV-003 a RF-MOV-006 (App equipo básica)
- RF-SEC-001, RF-SEC-002 (Seguridad básica)

### Fase 2 - Monitoreo y Paciente
- RF-WEB-001, RF-WEB-002 (Dashboard)
- RF-WEB-010, RF-WEB-011 (Monitoreo tiempo real)
- RF-MOV-009 a RF-MOV-013 (App paciente completa)
- RF-MOV-002 (Notificaciones push)
- RF-DISP-002 (Modo offline)

### Fase 3 - Optimización y Análisis
- RF-OPT-002, RF-OPT-003 (Optimización avanzada)
- RF-MOV-007, RF-MOV-008 (Funciones avanzadas equipo)
- RF-WEB-009 (Ajustes manuales)
- RF-SEC-003 (Auditoría completa)
- RF-INT-001, RF-INT-002 (Integraciones)

---

**Fin del Documento**
