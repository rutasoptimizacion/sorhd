# FlamenGO! - Sistema de Optimización de Rutas para Hospitalización Domiciliaria

**Route Optimization Platform for Home Hospitalization Services**

## Descripción del Proyecto

FlamenGO! es una plataforma integral de optimización de rutas diseñada específicamente para servicios de hospitalización domiciliaria. El sistema ayuda a los equipos clínicos a optimizar las rutas diarias de visitas considerando las habilidades del personal, la capacidad de los vehículos, las ventanas de tiempo y las restricciones geográficas.

## Características Principales

### 🚗 Optimización de Rutas Inteligente
- Algoritmos avanzados de optimización basados en Google OR-Tools
- Consideración de ventanas de tiempo, habilidades del personal y capacidad de vehículos
- Minimización de distancia y tiempo de viaje
- Balanceo de carga entre equipos

### 📱 Aplicación Móvil
- **Perfil Equipo Clínico**: Visualización de rutas, actualización de estado de visitas, rastreo GPS
- **Perfil Paciente**: Visualización de estado de visitas, rastreo en tiempo real del equipo (estilo Uber)

### 🖥️ Panel de Administración Web
- Gestión de recursos (personal, vehículos, pacientes, casos)
- Interfaz de planificación de rutas con visualización en mapa
- Dashboard de monitoreo en vivo con rastreo en tiempo real

### 📍 Rastreo en Tiempo Real
- Seguimiento GPS de vehículos
- Actualizaciones de ETA en tiempo real
- Notificaciones automáticas a pacientes

### 🔔 Sistema de Notificaciones
- Notificaciones push (Android/iOS)
- Fallback SMS para mayor confiabilidad
- Alertas automáticas de retrasos

## Arquitectura del Sistema

### Componentes Principales

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Panel Admin   │     │  App Móvil      │     │   Backend API   │
│   (React.js)    │────▶│  (React Native) │────▶│   (FastAPI)     │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                          │
                                                          ▼
                                                  ┌─────────────────┐
                                                  │  PostgreSQL +   │
                                                  │    PostGIS      │
                                                  └─────────────────┘
```

### Stack Tecnológico

#### Backend
- **Framework**: FastAPI (Python 3.11+)
- **Base de Datos**: PostgreSQL 15+ con extensión PostGIS
- **ORM**: SQLAlchemy con GeoAlchemy2
- **Optimización**: Google OR-Tools
- **Autenticación**: JWT con control de acceso basado en roles
- **Tiempo Real**: WebSocket para actualizaciones GPS
- **Notificaciones**: Firebase Cloud Messaging (FCM) / Apple Push Notification Service (APNS)

#### Panel de Administración
- **Framework**: React 18 + TypeScript
- **Build Tool**: Vite
- **Estado**: Redux Toolkit + React Query
- **UI**: Material-UI
- **Mapas**: Leaflet / Google Maps

#### Aplicación Móvil
- **Framework**: React Native
- **Estado**: Redux Toolkit + AsyncStorage
- **Mapas**: react-native-maps
- **Notificaciones**: Firebase (Android) + APNS (iOS)

## Inicio Rápido

### Requisitos Previos

- Python 3.11+
- Node.js 18+
- PostgreSQL 15+ con PostGIS
- Docker y Docker Compose (opcional)
- Xcode (para desarrollo iOS)
- Android Studio (para desarrollo Android)

### Instalación con Docker

```bash
# Clonar el repositorio
git clone <repository-url>
cd hdroutes

# Iniciar todos los servicios
docker-compose up

# El backend estará disponible en: http://localhost:8000
# El panel admin estará disponible en: http://localhost:5173
# PostgreSQL estará disponible en: localhost:5432
```

### Instalación Manual

#### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configurar base de datos
createdb sorhd
psql -d sorhd -c "CREATE EXTENSION postgis;"

# Ejecutar migraciones
alembic upgrade head

# Iniciar servidor
uvicorn app.main:app --reload
```

#### Panel de Administración

```bash
cd admin
npm install
npm run dev
```

#### Aplicación Móvil

```bash
cd mobile
npm install

# Para iOS
npx react-native run-ios

# Para Android
npx react-native run-android
```

## Estructura del Proyecto

```
hdroutes/
├── backend/                 # API FastAPI
│   ├── app/
│   │   ├── api/            # Endpoints de API
│   │   ├── core/           # Configuración y utilidades
│   │   ├── models/         # Modelos SQLAlchemy
│   │   ├── schemas/        # Schemas Pydantic
│   │   ├── services/       # Lógica de negocio
│   │   └── main.py         # Punto de entrada
│   ├── tests/              # Tests
│   ├── requirements.txt    # Dependencias Python
│   └── Dockerfile
├── admin/                   # Panel de administración React
│   ├── src/
│   │   ├── components/     # Componentes React
│   │   ├── hooks/          # Custom hooks
│   │   ├── services/       # Clientes API
│   │   ├── store/          # Estado Redux
│   │   ├── types/          # Tipos TypeScript
│   │   └── App.tsx
│   ├── package.json
│   └── vite.config.ts
├── mobile/                  # Aplicación React Native
│   ├── src/
│   │   ├── screens/        # Pantallas
│   │   ├── components/     # Componentes
│   │   ├── services/       # Clientes API
│   │   ├── store/          # Estado Redux
│   │   └── navigation/     # Navegación
│   ├── ios/                # Proyecto iOS
│   ├── android/            # Proyecto Android
│   └── package.json
├── specs/                   # Especificaciones técnicas
│   ├── requirements.md     # Requerimientos funcionales
│   └── design.md          # Documento de diseño
├── documents/              # Documentación adicional
├── CHECKLIST.md            # Lista de tareas de implementación
├── CLAUDE.md               # Instrucciones para Claude Code
└── docker-compose.yml      # Configuración Docker
```

## Documentación

- **[CHECKLIST.md](CHECKLIST.md)**: Lista detallada de tareas de implementación en 15 fases
- **[specs/requirements.md](specs/requirements.md)**: Requerimientos funcionales y no funcionales
- **[specs/design.md](specs/design.md)**: Documento de diseño del sistema
- **[CLAUDE.md](CLAUDE.md)**: Guía para trabajo con Claude Code

## Roles de Usuario

1. **Administrador**: Gestión completa del sistema, planificación de rutas, monitoreo en vivo
2. **Equipo Clínico**: Visualización de rutas asignadas, actualización de estado de visitas, navegación
3. **Paciente**: Visualización de estado de visita, rastreo en tiempo real del equipo

## Características de Seguridad

- Autenticación JWT con tokens de corta duración
- Control de acceso basado en roles (RBAC)
- Hashing de contraseñas con bcrypt
- Comunicación TLS 1.3
- Cifrado de base de datos en reposo
- Logging de auditoría para todas las mutaciones
- Protección contra inyección SQL
- Validación de entrada con Pydantic

## Requerimientos de Rendimiento

- Optimización de rutas (50 casos): < 60 segundos
- Tiempo de respuesta API (percentil 95): < 500ms
- Tiempo de carga de mapa (50 vehículos): < 2 segundos
- Latencia WebSocket: < 1 segundo
- Consultas de base de datos: < 100ms (percentil 95)
- Inicio en frío de app móvil: < 3 segundos

## Testing

```bash
# Backend
cd backend
pytest tests/ --cov=app --cov-report=term-missing

# Panel Admin
cd admin
npm run test

# Aplicación Móvil
cd mobile
npm test
```

## Despliegue

Ver [CHECKLIST.md](CHECKLIST.md) Fase 15 para instrucciones detalladas de despliegue.

## Estado del Proyecto

**Estado Actual**: En desarrollo - Fase 0 (Configuración inicial)

Ver [CHECKLIST.md](CHECKLIST.md) para el progreso detallado de implementación.

## Roadmap

### MVP (Versión 1.0) - Estimado: 2.5-3.5 meses
- ✅ Configuración del proyecto
- ⏳ Backend con autenticación y base de datos
- ⏳ Motor de optimización de rutas
- ⏳ Panel de administración web
- ⏳ Aplicación móvil (iOS/Android)
- ⏳ Sistema de notificaciones
- ⏳ Rastreo GPS en tiempo real

### Mejoras Futuras (Post-MVP)
- Geocodificación avanzada desde direcciones
- Integración con EHR/Ficha Clínica
- Análisis predictivo de duración de visitas
- Planificación de rutas multi-día
- Seguimiento de mantenimiento de vehículos
- Encuestas de satisfacción del paciente
- Mejoras de optimización con machine learning

## Contribución

Este proyecto es parte de un hackathon del Ministerio de Ciencia. Para contribuir:

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## Licencia

[Especificar licencia]

## Contacto

[Información de contacto del proyecto]

## Agradecimientos

- Ministerio de Ciencia por el apoyo al proyecto
- Google OR-Tools por las herramientas de optimización
- Comunidad open source de FastAPI, React, y React Native

---

**Versión**: 1.0  
**Última actualización**: 2025-11-14  
**Mantenedores**: Carlos Roa - github@CarlosRoa
