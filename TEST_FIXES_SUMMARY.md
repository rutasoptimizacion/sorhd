# Phase 5 Test Fixes Summary

## Date: 2025-11-15

## Issues Fixed

### 1. Missing Database Fixtures
**Problem:** Tests were failing with "fixture 'db' not found"
**Solution:** Added comprehensive database fixtures to `backend/tests/conftest.py`:
- `db_engine` - PostgreSQL engine (using docker-compose database)
- `db_session` / `db` - Database session with automatic cleanup
- `test_vehicle` - Sample vehicle for testing
- `test_patient` - Sample patient for testing  
- `test_case` - Sample case for testing
- `test_active_route` - Sample active route with visit
- `test_visit` - Sample visit for testing

### 2. Haversine Distance Calculation
**Problem:** Tests expected 111,320m per degree but got 111,195m
**Solution:** Updated test expectations in `test_haversine_provider.py` to use more accurate value (111,195m)
**Files Modified:**
- `backend/tests/services/distance/test_haversine_provider.py` (lines 91-116)

### 3. Distance Service Provider Selection  
**Problem:** `test_get_primary_provider` expected Haversine but got OSRM
**Solution:** Modified DistanceService to only initialize OSRM when explicitly configured
**Files Modified:**
- `backend/app/services/distance/distance_service.py` (line 60: added `if osrm_base_url is not None`)

### 4. SQLite vs PostgreSQL
**Problem:** SQLite doesn't support PostGIS Geography types
**Solution:** Changed test database from SQLite to PostgreSQL (using docker-compose postgres service)
**Files Modified:**
- `backend/tests/conftest.py` (db_engine now uses settings.DATABASE_URL)

## Test Results

**Passing Tests:** 30/60 (50%)
- ✅ All distance calculation tests  
- ✅ All haversine provider tests
- ✅ All distance service tests

**Failing Tests:** 30/60 (50%)  
- ❌ Location tracker tests (enum serialization issue)
- ❌ Route tracker tests (enum serialization issue)
- ❌ Tracking integration tests (enum serialization issue)

## Known Issues

### Vehicle Status Enum Serialization
**Problem:** VehicleStatus enum is being serialized as "AVAILABLE" instead of "available"
**Status:** Under investigation
**Details:**
- Database enum has correct lowercase values: 'available', 'in_use', 'maintenance', 'unavailable'
- Python enum defined correctly with str, enum.Enum and lowercase values
- SQLAlchemy appears to be using enum NAME instead of VALUE when inserting

**Workaround Needed:**
The fixture currently uses string "available" directly, but SQLAlchemy is still converting it to "AVAILABLE" before sending to database.

## Next Steps

1. Investigate SQLAlchemy enum handling in BaseModel or Vehicle model
2. Check if there's a custom enum type handler that needs to be configured  
3. Consider using native_enum=False in Column definition as workaround
4. Once enum issue is resolved, all 60 tests should pass

## Files Modified

1. `backend/tests/conftest.py` - Added database fixtures
2. `backend/tests/services/distance/test_haversine_provider.py` - Updated distance expectations
3. `backend/app/services/distance/distance_service.py` - Fixed OSRM initialization

## How to Run Tests

```bash
# Run all Phase 5 tests
docker-compose exec backend pytest tests/services/test_location_tracker.py tests/services/test_route_tracker.py tests/services/test_tracking_integration.py tests/services/distance/ -v

# Run just passing tests
docker-compose exec backend pytest tests/services/distance/ -v

# Run single failing test for debugging
docker-compose exec backend pytest tests/services/test_location_tracker.py::test_record_location -vvs
```

