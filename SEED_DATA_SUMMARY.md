# Script de Seed para Base de Datos - Resumen

## ✅ Completado

Se ha creado exitosamente un script completo para poblar la base de datos con datos de prueba realistas para probar la **Phase 9 - Route Planning** del sistema FlamenGO!.

## 📁 Archivos Creados

1. **`backend/scripts/seed_database.py`** - Script principal de seed
2. **`backend/scripts/README.md`** - Documentación completa actualizada

## 📊 Datos Generados

El script crea los siguientes datos:

### 🎯 Habilidades (10)
- Enfermería
- Medicina General
- Kinesiología
- Terapia Ocupacional
- Fonoaudiología
- Nutrición
- Psicología
- Trabajo Social
- Cuidados Paliativos
- Manejo de Heridas

### 🏥 Tipos de Atención (10)
1. **Control de Signos Vitales** (30 min) - Requiere: Enfermería
2. **Curación de Heridas** (45 min) - Requiere: Enfermería, Manejo de Heridas
3. **Terapia Respiratoria** (60 min) - Requiere: Kinesiología
4. **Control Médico** (45 min) - Requiere: Medicina General, Enfermería
5. **Terapia Ocupacional** (60 min) - Requiere: Terapia Ocupacional
6. **Evaluación Nutricional** (45 min) - Requiere: Nutrición
7. **Apoyo Psicológico** (60 min) - Requiere: Psicología
8. **Cuidados Paliativos** (90 min) - Requiere: Medicina General, Enfermería, Cuidados Paliativos
9. **Terapia del Habla** (60 min) - Requiere: Fonoaudiología
10. **Visita Social** (45 min) - Requiere: Trabajo Social

### 👥 Personal de Salud (15)
- Enfermeros/as (4) - Con diferentes especializaciones
- Médicos/as (2) - Medicina general y cuidados paliativos
- Kinesiólogos/as (2)
- Terapeuta Ocupacional (1)
- Nutricionista (1)
- Psicólogo/a (1)
- Fonoaudiólogo/a (1)
- Trabajador/a Social (1)
- Técnicos y auxiliares (2)

**Características:**
- Todos trabajan de 08:00 a 17:00
- Tienen diferentes combinaciones de habilidades
- Ubicaciones iniciales distribuidas en Santiago

### 🚗 Vehículos (5)
- **VEH-001** (ABCD12): Capacidad 3, con Oxígeno, Camilla, Botiquín
- **VEH-002** (EFGH34): Capacidad 2, con Oxígeno, Botiquín
- **VEH-003** (IJKL56): Capacidad 4, con Oxígeno, Camilla, Botiquín, Silla de ruedas
- **VEH-004** (MNOP78): Capacidad 2, con Botiquín
- **VEH-005** (QRST90): Capacidad 3, con Oxígeno, Botiquín, Silla de ruedas

**Características:**
- Todos en estado "available"
- Ubicaciones base distribuidas en Santiago
- Diferentes capacidades y recursos médicos

### 🏠 Pacientes (70)
- Nombres y apellidos chilenos realistas
- Teléfonos con formato chileno (+569...)
- Correos electrónicos
- Direcciones en calles de Santiago
- Ubicaciones geográficas distribuidas en Santiago (±11km del centro)

### 📋 Casos (55)
**Programados para mañana** con:

**Por Prioridad:**
- 🔴 Urgente (URGENT): ~5 casos
- 🟠 Alta (HIGH): ~12 casos
- 🟡 Media (MEDIUM): ~29 casos
- 🟢 Baja (LOW): ~9 casos

**Por Ventana Horaria:**
- 🌅 AM (08:00-12:00): ~14 casos
- 🌆 PM (12:00-17:00): ~10 casos
- ⏰ Específica (2 horas): ~15 casos
- 🔄 Flexible (ANYTIME): ~16 casos

**Características:**
- Duraciones realistas según tipo de atención (30-90 minutos)
- Ubicaciones corresponden a pacientes reales
- Estado: PENDING (listo para optimización)

## 🚀 Cómo Usar el Script

### Opción 1: Ejecución desde Docker (Recomendado)

```bash
cd backend

# Poblar la base de datos
docker exec sorhd-backend python /app/scripts/seed_database.py --clean --force

# Ver ayuda
docker exec sorhd-backend python /app/scripts/seed_database.py --help
```

### Opción 2: Ejecución Local

```bash
cd backend
source venv/bin/activate

# Instalar dependencias si es necesario
pip install -r requirements.txt

# Poblar la base de datos
python scripts/seed_database.py --clean --force
```

## 🎛️ Opciones Disponibles

- `--force` o `-f`: Ejecutar sin confirmación (útil para CI/CD)
- `--clean` o `-c`: Limpiar datos existentes antes de poblar (⚠️ CUIDADO: Borra todos los datos)
- `--help`: Mostrar ayuda

## 📍 Datos Geográficos

- **Ubicación central**: Santiago, Chile (-33.4489, -70.6693)
- **Radio de distribución**: ~11km del centro
- **Sistema de coordenadas**: WGS 84 (EPSG:4326)
- **Formato PostGIS**: GEOGRAPHY(POINT, 4326)

## ✅ Verificación

Para verificar que los datos se crearon correctamente:

```bash
docker exec sorhd-backend python -c "
from sqlalchemy import create_engine, text
import os

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://sorhd_user:sorhd_password@postgres:5432/sorhd')
engine = create_engine(DATABASE_URL)

with engine.connect() as conn:
    result = conn.execute(text('''
        SELECT '\''skills'\'' as tabla, COUNT(*) FROM skills
        UNION ALL SELECT '\''care_types'\'', COUNT(*) FROM care_types
        UNION ALL SELECT '\''personnel'\'', COUNT(*) FROM personnel
        UNION ALL SELECT '\''vehicles'\'', COUNT(*) FROM vehicles
        UNION ALL SELECT '\''patients'\'', COUNT(*) FROM patients
        UNION ALL SELECT '\''cases'\'', COUNT(*) FROM cases;
    '''))
    for row in result:
        print(f'{row[0]}: {row[1]}')
"
```

**Salida esperada:**
```
skills: 10
care_types: 10
personnel: 15
vehicles: 5
patients: 70
cases: 55
```

## 🎯 Próximos Pasos para Probar Phase 9

1. **Iniciar los servicios:**
   ```bash
   # Terminal 1: Backend
   cd backend
   docker-compose up backend

   # Terminal 2: Admin Panel
   cd admin
   npm run dev
   ```

2. **Acceder al Admin Panel:**
   - URL: http://localhost:5173
   - Usuario: `admin`
   - Contraseña: `admin123`

3. **Ir a Planificación de Rutas:**
   - Navegar a la sección de "Planificación de Rutas"
   - Seleccionar la fecha de mañana
   - Verás 55 casos disponibles para optimizar

4. **Seleccionar recursos:**
   - Seleccionar algunos o todos los 55 casos
   - Seleccionar los 5 vehículos disponibles
   - Asignar personal a cada vehículo

5. **Optimizar:**
   - Hacer clic en "Optimizar Rutas"
   - El sistema debe generar rutas optimizadas
   - Ver resultados en mapa y tabla

## 🔧 Troubleshooting

### Error: "Cannot connect to database"
```bash
docker-compose ps  # Verificar que postgres esté corriendo
docker-compose up -d postgres
```

### Error: "Table does not exist"
```bash
docker exec sorhd-backend alembic upgrade head
```

### Quiero resetear los datos
```bash
# Opción 1: Usando el script con --clean
docker exec sorhd-backend python /app/scripts/seed_database.py --clean --force

# Opción 2: Bajar y recrear el contenedor
docker-compose down
docker volume rm hdroutes_postgres_data
docker-compose up -d postgres
sleep 5
docker exec sorhd-backend alembic upgrade head
docker exec sorhd-backend python /app/scripts/seed_database.py --force
```

## 📝 Notas Importantes

1. **Los casos se crean para MAÑANA** - Esto facilita las pruebas sin tener que modificar fechas
2. **Datos realistas** - Todos los nombres, direcciones y datos son apropiados para Chile
3. **Distribución balanceada** - Las prioridades y ventanas horarias están distribuidas realísticamente
4. **Skill matching** - Los tipos de atención requieren habilidades específicas que el personal tiene
5. **Listo para Phase 9** - Los datos están diseñados específicamente para probar la optimización de rutas

## 🎉 Resultado

La base de datos está ahora poblada con **265 registros** de datos de prueba realistas:
- ✅ 10 habilidades
- ✅ 10 tipos de atención
- ✅ 15 personal
- ✅ 5 vehículos
- ✅ 70 pacientes
- ✅ 55 casos

**¡Todo listo para probar la Phase 9 - Route Planning!**

---

**Creado:** 2025-11-15
**Versión:** 1.0
**Autor:** Claude Code
