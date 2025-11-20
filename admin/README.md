# FlamenGO! Admin Panel

Panel de administración web para el Sistema de Optimización de Rutas para Hospitalización Domiciliaria.

## Estado de Implementación

✅ **Phase 7: Admin Panel - Foundation** - Completada

### Características Implementadas

#### 7.1 Project Initialization
- ✅ React 18 + TypeScript + Vite configurado
- ✅ Dependencias core instaladas (React Router, Redux Toolkit, Material-UI)
- ✅ TypeScript configurado con strict mode
- ✅ Path aliases configurados (@/*)

#### 7.2 State Management
- ✅ Redux Toolkit store configurado
- ✅ authSlice implementado con persistencia en localStorage
- ✅ Redux DevTools habilitado
- ✅ React Query configurado para server state
- ✅ Hooks personalizados (useAppDispatch, useAppSelector)

#### 7.3 API Client
- ✅ Axios client configurado con base URL
- ✅ Request interceptor para auth token
- ✅ Response interceptor para manejo de errores
- ✅ Refresh token automático implementado
- ✅ authService con login/logout/refresh

#### 7.4 Authentication UI
- ✅ Login page con validación (react-hook-form + zod)
- ✅ Token storage en localStorage
- ✅ PrivateRoute wrapper para rutas protegidas
- ✅ Logout functionality

#### 7.5 Layout Components
- ✅ Layout principal con Header y Sidebar
- ✅ Header con menú de usuario
- ✅ Sidebar con navegación
- ✅ Responsive design (mobile + desktop)
- ✅ Material-UI theming

#### 7.6 Routing
- ✅ React Router configurado
- ✅ Rutas protegidas implementadas
- ✅ 404 Not Found page
- ✅ Navegación funcional

#### 7.7 Common Components
- ✅ DataTable (sorting, filtering, pagination)
- ✅ FormField (react-hook-form integration)
- ✅ ConfirmDialog
- ✅ LoadingSpinner
- ✅ ErrorMessage
- ✅ SuccessMessage

### Páginas Implementadas

1. **LoginPage** (`/login`) - Autenticación de usuarios
2. **DashboardPage** (`/`) - Panel principal con estadísticas
3. **NotFoundPage** (`/404`) - Página de error 404

### Rutas Placeholder

Las siguientes rutas están creadas pero muestran contenido de marcador:
- `/personnel` - Personal
- `/vehicles` - Vehículos
- `/patients` - Pacientes
- `/cases` - Casos
- `/planning` - Planificación de rutas
- `/monitoring` - Monitoreo en vivo
- `/notifications` - Notificaciones
- `/reports` - Reportes

Estas rutas se implementarán en **Phase 8: Resource Management**.

## Configuración

### Variables de Entorno

Crear archivo `.env` basado en `.env.example`:

```env
VITE_API_BASE_URL=http://localhost:8000/api/v1
VITE_WS_BASE_URL=ws://localhost:8000
```

### Instalación

```bash
npm install
```

### Desarrollo

```bash
npm run dev
```

El servidor de desarrollo se iniciará en http://localhost:5173

### Build de Producción

```bash
npm run build
```

### Preview de Build

```bash
npm run preview
```

### Linting

```bash
npm run lint
```

### Formateo de Código

```bash
npm run format
```

## Estructura del Proyecto

```
admin/
├── src/
│   ├── components/
│   │   ├── auth/
│   │   │   └── PrivateRoute.tsx
│   │   ├── common/
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorMessage.tsx
│   │   │   ├── SuccessMessage.tsx
│   │   │   ├── ConfirmDialog.tsx
│   │   │   ├── DataTable.tsx
│   │   │   ├── FormField.tsx
│   │   │   └── index.ts
│   │   └── layout/
│   │       ├── Header.tsx
│   │       ├── Sidebar.tsx
│   │       └── Layout.tsx
│   ├── hooks/
│   │   ├── useAppDispatch.ts
│   │   ├── useAppSelector.ts
│   │   └── index.ts
│   ├── lib/
│   │   └── queryClient.ts
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── DashboardPage.tsx
│   │   └── NotFoundPage.tsx
│   ├── services/
│   │   ├── api.ts
│   │   └── authService.ts
│   ├── store/
│   │   ├── authSlice.ts
│   │   └── index.ts
│   ├── types/
│   │   └── index.ts
│   ├── App.tsx
│   ├── main.tsx
│   └── index.css
├── .env
├── .env.example
├── .eslintrc.cjs
├── .prettierrc.json
├── package.json
├── tsconfig.json
├── vite.config.ts
└── README.md
```

## Tecnologías Utilizadas

### Core
- **React 18** - UI library
- **TypeScript** - Type safety
- **Vite** - Build tool

### State Management
- **Redux Toolkit** - Global state
- **React Query** - Server state

### Routing
- **React Router v6** - Client-side routing

### UI Framework
- **Material-UI (MUI)** - Component library
- **@mui/icons-material** - Icons

### Forms & Validation
- **react-hook-form** - Form handling
- **zod** - Schema validation

### HTTP Client
- **axios** - API requests

### Maps (Future)
- **Leaflet** - Map visualization
- **react-leaflet** - React bindings

### Real-time (Future)
- **socket.io-client** - WebSocket client

## Próximos Pasos

### Phase 8: Resource Management (5-6 días)
- Implementar CRUD para Personal
- Implementar CRUD para Vehículos
- Implementar CRUD para Pacientes
- Implementar CRUD para Casos
- Implementar CRUD para Care Types y Skills
- Agregar validación de datos
- Agregar audit logging

## Notas de Desarrollo

### Autenticación
- Los tokens se almacenan en localStorage
- El refresh token se maneja automáticamente
- Si el refresh falla, se redirige al login
- El estado de autenticación persiste entre recargas

### API Client
- Base URL configurada vía variable de entorno
- Todos los requests incluyen auth token automáticamente
- Los errores se manejan globalmente
- Timeout de 30 segundos

### Routing
- Todas las rutas excepto /login requieren autenticación
- Los usuarios no autenticados son redirigidos a /login
- Las rutas inválidas redirigen a /404

### Theming
- Material-UI theme customizable en App.tsx
- Responsive design por defecto
- Dark mode soportado (configurar en theme)

## Soporte

Para reportar problemas o sugerir mejoras, contactar al equipo de desarrollo.

---

**Versión:** 1.0
**Última actualización:** 2025-11-15
**Estado:** Phase 7 Completa
