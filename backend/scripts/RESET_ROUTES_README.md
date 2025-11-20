# Script de Reseteo de Rutas

Este script elimina rutas existentes y resetea el estado de los casos asociados para que puedan ser reasignados con el nuevo algoritmo de selección de personal optimizado.

## ¿Por qué usar este script?

Después de corregir el bug de asignación de personal, las rutas antiguas todavía tienen todo el personal del sistema asignado. Este script te permite limpiar esas rutas y crear nuevas con la asignación optimizada.

## Ejecución desde Docker (Recomendado)

⚠️ **IMPORTANTE**: Al ejecutar desde Docker, agrega `--yes` o `-y` para confirmar automáticamente (no hay TTY interactivo).

### Opción 1: Eliminar TODAS las rutas

```bash
docker-compose exec backend python scripts/reset_routes.py --all
```

### Opción 2: Eliminar rutas por fecha

```bash
# Eliminar rutas del 17 de noviembre de 2025
docker-compose exec backend python scripts/reset_routes.py --date 2025-11-17 --yes
```

### Opción 3: Eliminar rutas por estado

```bash
# Eliminar solo rutas en estado 'draft'
docker-compose exec backend python scripts/reset_routes.py --status draft -y

# Eliminar solo rutas 'active'
docker-compose exec backend python scripts/reset_routes.py --status active --yes
```

### Opción 4: Combinar filtros

```bash
# Eliminar rutas del 17 de noviembre que estén en 'draft'
docker-compose exec backend python scripts/reset_routes.py --date 2025-11-17 --status draft -y
```

## Estados válidos

- `draft` - Rutas en borrador
- `active` - Rutas activas
- `in_progress` - Rutas en progreso
- `completed` - Rutas completadas
- `cancelled` - Rutas canceladas

## Interactivo vs No-interactivo

- **Sin --yes**: El script mostrará un resumen y pedirá confirmación
- **Con --yes o -y**: Eliminará las rutas automáticamente sin pedir confirmación (requerido para Docker)
- **Con --all**: Eliminará todas las rutas inmediatamente sin confirmación

## ¿Qué hace el script?

1. **Busca** las rutas que coincidan con los criterios especificados
2. **Muestra** un resumen de lo que se eliminará
3. **Pide confirmación** (excepto con --all)
4. **Elimina** las rutas (las relaciones en cascada eliminan automáticamente):
   - Asociaciones route_personnel
   - Visitas (visits)
5. **Resetea** el estado de los casos asociados de 'assigned' a 'pending'
6. **Muestra** estadísticas finales

## Ejemplo de salida

```
============================================================
RESUMEN DE RUTAS A ELIMINAR
============================================================
Total de rutas: 12

Por estado:
  - draft: 3
  - active: 7
  - completed: 2

Total de visitas a eliminar: 48
Total de casos a resetear: 30
============================================================

¿Desea continuar con la eliminación? (s/n): s

📋 Recolectando casos asociados...
🗑️  Eliminando 12 rutas...
✅ 12 rutas eliminadas correctamente

🔄 Reseteando 30 casos a estado 'pending'...
✅ 30 casos reseteados a 'pending'

============================================================
✅ OPERACIÓN COMPLETADA EXITOSAMENTE
============================================================

Resumen:
  - Rutas eliminadas: 12
  - Visitas eliminadas: 48
  - Casos reseteados: 30
```

## Verificar el resultado

Después de ejecutar el script, puedes verificar que las rutas se eliminaron:

```bash
# Ver todas las rutas restantes
curl -s http://localhost:8000/api/v1/routes \
  -H "Authorization: Bearer <TOKEN>" | python3 -m json.tool

# Crear una nueva optimización y verificar el personal asignado
# (debería mostrar solo 2-3 personas en lugar de 15)
```

## Troubleshooting

### Error: "ModuleNotFoundError"

Si obtienes este error, asegúrate de que estás ejecutando el script desde el contenedor Docker:

```bash
# ✅ Correcto
docker-compose exec backend python scripts/reset_routes.py --all

# ❌ Incorrecto (requiere instalar dependencias localmente)
python backend/scripts/reset_routes.py --all
```

### Error: "No se encontraron rutas"

Verifica los filtros que estás usando:

```bash
# Listar todas las rutas primero
docker-compose exec backend python -c "
from app.core.database import SessionLocal
from app.models.route import Route
db = SessionLocal()
routes = db.query(Route).all()
print(f'Total rutas: {len(routes)}')
for r in routes:
    print(f'  - ID: {r.id}, Fecha: {r.route_date}, Estado: {r.status}')
db.close()
"
```

## Recuperación

⚠️ **IMPORTANTE**: Este script elimina datos de forma permanente. No hay undo.

Si necesitas mantener un respaldo antes de ejecutar el script:

```bash
# Hacer backup de la base de datos
docker-compose exec postgres pg_dump -U postgres hdroutes > backup_$(date +%Y%m%d_%H%M%S).sql

# Ejecutar el script
docker-compose exec backend python scripts/reset_routes.py --all

# Si necesitas restaurar (opcional)
# docker-compose exec -T postgres psql -U postgres hdroutes < backup_YYYYMMDD_HHMMSS.sql
```

## Ver ayuda del script

```bash
docker-compose exec backend python scripts/reset_routes.py --help
```
