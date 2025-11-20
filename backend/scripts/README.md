# Scripts de Base de Datos

Este directorio contiene scripts útiles para gestionar la base de datos del sistema SOR-HD.

## Scripts Disponibles

### 1. `create_admin.py` - Crear Usuario Administrador

Crea un usuario administrador inicial para acceder al sistema.

**Uso:**
```bash
cd backend
python scripts/create_admin.py
```

**Credenciales por defecto:**
- Usuario: `admin`
- Contraseña: `admin123`
- Rol: `admin`

⚠️ **IMPORTANTE:** Cambia la contraseña después del primer login.

---

### 2. `seed_database.py` - Poblar Base de Datos con Datos de Prueba

Crea datos de prueba realistas para probar el sistema, especialmente útil para la **Phase 9 - Route Planning**.

**Datos generados:**
- ✅ **10 Habilidades** (Enfermería, Medicina, Kinesiología, etc.)
- ✅ **10 Tipos de Atención** (Control de signos vitales, curaciones, terapias, etc.)
- ✅ **15 Personal de Salud** con diversas habilidades
- ✅ **5 Vehículos** con diferentes capacidades y recursos
- ✅ **70 Pacientes** distribuidos por Santiago
- ✅ **55 Casos** programados para mañana (con diferentes prioridades y ventanas horarias)

**Características de los datos:**
- 📍 Ubicaciones realistas en Santiago de Chile
- 📱 Teléfonos y correos con formato chileno
- ⏰ Ventanas horarias variadas (AM, PM, específicas, flexibles)
- 🚨 Distribución realista de prioridades (baja, media, alta, urgente)
- 👥 Personal con combinaciones apropiadas de habilidades
- 🚗 Vehículos con recursos médicos específicos

**Requisitos previos:**
1. Base de datos PostgreSQL con PostGIS corriendo
2. Migraciones aplicadas (ver abajo)
3. Variables de entorno configuradas (o usar valores por defecto)

**Uso básico:**
```bash
cd backend

# Asegúrate de que la base de datos esté corriendo
docker-compose up -d postgres

# Aplica las migraciones (si no lo has hecho)
alembic upgrade head

# Ejecuta el script de seed (interactivo)
python scripts/seed_database.py

# O ejecútalo desde Docker (recomendado)
docker exec sorhd-backend python /app/scripts/seed_database.py
```

**Opciones de línea de comandos:**

```bash
# Ejecutar sin confirmación (útil para CI/CD o scripts automatizados)
python scripts/seed_database.py --force
# o
python scripts/seed_database.py -f

# Limpiar datos existentes y poblar desde cero (CUIDADO: Borra todos los datos)
python scripts/seed_database.py --clean --force
# o
python scripts/seed_database.py -c -f

# Ver ayuda
python scripts/seed_database.py --help
```

**Variables de entorno:**
El script usa la variable `DATABASE_URL` del entorno. Si no está configurada, usa:
```
postgresql://sorhd_user:sorhd_password@localhost:5432/sorhd
```

Para usar una URL diferente:
```bash
export DATABASE_URL="postgresql://usuario:password@host:puerto/database"
python scripts/seed_database.py
```

**Salida esperada:**
```
🌱 POBLANDO BASE DE DATOS CON DATOS DE PRUEBA
============================================================
📚 Creando habilidades...
✅ 10 habilidades creadas

🏥 Creando tipos de atención...
✅ 10 tipos de atención creados

👥 Creando personal de salud...
✅ 15 personal de salud creado

🚗 Creando vehículos...
✅ 5 vehículos creados

🏠 Creando pacientes...
✅ 70 pacientes creados

📋 Creando casos para mañana...
✅ 55 casos creados para 16/11/2025

============================================================
📊 RESUMEN DE DATOS CREADOS
============================================================
✅ Habilidades: 10
✅ Tipos de atención: 10
✅ Personal: 15
✅ Vehículos: 5
✅ Pacientes: 70
✅ Casos: 55
============================================================

📅 Casos por prioridad:
   LOW: 5
   MEDIUM: 33
   HIGH: 14
   URGENT: 3

⏰ Casos por ventana horaria:
   AM: 17
   PM: 16
   SPECIFIC: 11
   ANYTIME: 11

============================================================
🎉 Base de datos poblada exitosamente!
============================================================
```

**Notas importantes:**
- ⚠️ Si la base de datos ya contiene datos, el script preguntará si deseas continuar
- 📅 Los casos se crean para **mañana** para facilitar las pruebas
- 🔄 Puedes ejecutar el script múltiples veces para agregar más datos
- 🧹 Para limpiar la base de datos: `alembic downgrade base && alembic upgrade head`

---

## Workflow Completo para Pruebas

### Configuración inicial completa:

```bash
# 1. Clonar el repositorio y entrar al backend
cd backend

# 2. Crear y activar entorno virtual
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Levantar la base de datos con Docker
docker-compose up -d postgres

# 5. Esperar a que PostgreSQL esté listo (unos segundos)
sleep 5

# 6. Aplicar migraciones
alembic upgrade head

# 7. Crear usuario administrador
python scripts/create_admin.py

# 8. Poblar con datos de prueba
python scripts/seed_database.py

# 9. Iniciar el backend
uvicorn app.main:app --reload
```

### Probar la Phase 9 - Route Planning:

```bash
# Terminal 1: Backend
cd backend
source venv/bin/activate
uvicorn app.main:app --reload

# Terminal 2: Admin Panel
cd admin
npm install  # Solo la primera vez
npm run dev

# Abre el navegador en: http://localhost:5173
# Login: admin / admin123
# Ve a: Planificación de Rutas
# Selecciona casos y vehículos
# Haz clic en "Optimizar Rutas"
```

---

## Troubleshooting

### Error: "Cannot connect to database"
```bash
# Verifica que PostgreSQL esté corriendo
docker-compose ps

# Si no está corriendo, inícialo
docker-compose up -d postgres

# Verifica los logs
docker-compose logs postgres
```

### Error: "PostGIS extension not found"
```bash
# Conéctate a la base de datos
docker-compose exec postgres psql -U sorhd_user -d sorhd

# Crea la extensión
CREATE EXTENSION IF NOT EXISTS postgis;
\q
```

### Error: "Table does not exist"
```bash
# Aplica las migraciones
alembic upgrade head
```

### Quiero resetear toda la base de datos
```bash
# Opción 1: Hacer downgrade y upgrade
alembic downgrade base
alembic upgrade head

# Opción 2: Recrear el contenedor de PostgreSQL
docker-compose down
docker volume rm hdroutes_postgres_data  # CUIDADO: Esto borra todos los datos
docker-compose up -d postgres
sleep 5
alembic upgrade head
```

---

## Validación de Datos

Para verificar que los datos se crearon correctamente:

```bash
# Conéctate a la base de datos
docker-compose exec postgres psql -U sorhd_user -d sorhd

# Verifica las tablas
\dt

# Cuenta los registros
SELECT 'skills' as tabla, COUNT(*) FROM skills
UNION ALL
SELECT 'care_types', COUNT(*) FROM care_types
UNION ALL
SELECT 'personnel', COUNT(*) FROM personnel
UNION ALL
SELECT 'vehicles', COUNT(*) FROM vehicles
UNION ALL
SELECT 'patients', COUNT(*) FROM patients
UNION ALL
SELECT 'cases', COUNT(*) FROM cases;

# Ver casos de mañana
SELECT c.id, p.name as paciente, ct.name as tipo_atencion, c.priority, c.time_window_type
FROM cases c
JOIN patients p ON c.patient_id = p.id
JOIN care_types ct ON c.care_type_id = ct.id
WHERE c.scheduled_date::date = CURRENT_DATE + 1
ORDER BY c.priority DESC, c.time_window_type;

\q
```

---

## Próximos Scripts (Futuros)

- `backup_database.py` - Crear respaldos de la base de datos
- `restore_database.py` - Restaurar desde un respaldo
- `clean_old_data.py` - Limpiar datos antiguos (location_logs, audit_logs)
- `generate_reports.py` - Generar reportes de uso y estadísticas

---

**Última actualización:** 2025-11-15
