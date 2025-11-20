# Notification System - Setup Guide

Complete guide for setting up and using the FlamenGO! notification system.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Setup Instructions](#setup-instructions)
  - [1. Firebase Cloud Messaging (FCM)](#1-firebase-cloud-messaging-fcm)
  - [2. Apple Push Notification Service (APNS)](#2-apple-push-notification-service-apns)
  - [3. Twilio SMS](#3-twilio-sms)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [API Endpoints](#api-endpoints)
- [Testing](#testing)
- [Troubleshooting](#troubleshooting)

---

## Overview

The notification system provides multi-channel messaging with automatic fallback:

- **Push Notifications** (FCM for Android, APNS for iOS)
- **SMS Notifications** (Twilio)
- **Automatic Fallback** (Push → SMS)

All notifications are in **Spanish** and support parameterized templates.

---

## Architecture

```
┌─────────────────┐
│ Notification    │
│ Service         │
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
┌───▼──┐  ┌──▼───┐
│ Push │  │ SMS  │
└───┬──┘  └──┬───┘
    │         │
  ┌─┴─┐     ┌┴──┐
  │FCM│     │TWL│
  │APN│     └───┘
  └───┘
```

### Components

1. **NotificationService** - Main orchestrator
2. **PushNotificationProvider** - Abstract interface
   - FCMProvider (Android)
   - APNSProvider (iOS)
3. **SMSProvider** - Abstract interface
   - TwilioSMSProvider

---

## Setup Instructions

### 1. Firebase Cloud Messaging (FCM)

**Purpose:** Push notifications for Android devices

#### Steps:

1. **Create Firebase Project**
   - Go to [Firebase Console](https://console.firebase.google.com/)
   - Click "Add Project"
   - Follow the wizard

2. **Enable Cloud Messaging**
   - In project settings, go to "Cloud Messaging" tab
   - Note the Server Key (for reference)

3. **Generate Service Account**
   - Go to Project Settings → Service Accounts
   - Click "Generate New Private Key"
   - Download the JSON file
   - Save as `firebase-service-account.json`

4. **Add Android App**
   - Click "Add App" → Android
   - Enter package name: `com.sorhd.app`
   - Download `google-services.json`
   - Add SHA-1 certificate fingerprint

5. **Set Environment Variable**
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-service-account.json
   ```

   Or add to `.env`:
   ```
   GOOGLE_APPLICATION_CREDENTIALS=/path/to/firebase-service-account.json
   ```

#### Test FCM:

```python
from app.services.notification_providers import FCMProvider
from app.services.notification_service import NotificationPayload

provider = FCMProvider()
payload = NotificationPayload(
    title="Test",
    body="FCM is working!"
)

result = await provider.send("device_token_here", payload)
print(result.success)  # True if successful
```

---

### 2. Apple Push Notification Service (APNS)

**Purpose:** Push notifications for iOS devices

#### Steps:

1. **Create App ID**
   - Go to [Apple Developer](https://developer.apple.com/)
   - Certificates, Identifiers & Profiles
   - Identifiers → App IDs → Create new
   - Bundle ID: `com.sorhd.app`
   - Enable "Push Notifications" capability

2. **Create APNs Key**
   - Keys → Create new key
   - Select "Apple Push Notifications service (APNs)"
   - Download the `.p8` file
   - **IMPORTANT:** Save the Key ID and Team ID

3. **Configure App in Xcode**
   - Open iOS project in Xcode
   - Signing & Capabilities → Add Push Notifications
   - Ensure Bundle ID matches

4. **Set Environment Variables**
   ```bash
   export APNS_TEAM_ID=YOUR_TEAM_ID
   export APNS_KEY_ID=YOUR_KEY_ID
   export APNS_KEY_FILE=/path/to/AuthKey_KEYID.p8
   export APNS_BUNDLE_ID=com.sorhd.app
   export APNS_USE_SANDBOX=true  # false in production
   ```

   Or add to `.env`:
   ```
   APNS_TEAM_ID=ABC1234567
   APNS_KEY_ID=XYZ9876543
   APNS_KEY_FILE=/path/to/AuthKey_XYZ9876543.p8
   APNS_BUNDLE_ID=com.sorhd.app
   APNS_USE_SANDBOX=true
   ```

#### Test APNS:

```python
from app.services.notification_providers import APNSProvider
from app.services.notification_service import NotificationPayload

provider = APNSProvider(
    team_id="ABC1234567",
    key_id="XYZ9876543",
    key_file="/path/to/AuthKey_XYZ9876543.p8",
    bundle_id="com.sorhd.app",
    use_sandbox=True
)

payload = NotificationPayload(
    title="Test",
    body="APNS is working!"
)

result = await provider.send("device_token_here", payload)
print(result.success)
```

---

### 3. Twilio SMS

**Purpose:** SMS notifications (fallback when push fails)

#### Steps:

1. **Create Twilio Account**
   - Go to [Twilio](https://www.twilio.com/)
   - Sign up for free trial (includes credits)

2. **Get Phone Number**
   - Phone Numbers → Buy a Number
   - Choose a Chilean number (+56) if available
   - Or use any number and configure international SMS

3. **Get Credentials**
   - Dashboard → Account Info
   - Note: Account SID and Auth Token

4. **Set Environment Variables**
   ```bash
   export TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   export TWILIO_AUTH_TOKEN=your_auth_token_here
   export TWILIO_FROM_PHONE=+56912345678
   ```

   Or add to `.env`:
   ```
   TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
   TWILIO_AUTH_TOKEN=your_auth_token_here
   TWILIO_FROM_PHONE=+56912345678
   ```

#### Test Twilio:

```python
from app.services.notification_providers import TwilioSMSProvider

provider = TwilioSMSProvider(
    account_sid="ACxxxxx",
    auth_token="your_token",
    from_phone="+56912345678"
)

result = await provider.send(
    phone_number="+56987654321",
    message="Twilio is working!"
)
print(result.success)
```

---

## Configuration

### Complete `.env` Example:

```bash
# ===========================
# Notification System
# ===========================

# FCM (Android)
GOOGLE_APPLICATION_CREDENTIALS=/app/credentials/firebase-service-account.json

# APNS (iOS)
APNS_TEAM_ID=ABC1234567
APNS_KEY_ID=XYZ9876543
APNS_KEY_FILE=/app/credentials/AuthKey_XYZ9876543.p8
APNS_BUNDLE_ID=com.sorhd.app
APNS_USE_SANDBOX=false  # true for development

# Twilio (SMS)
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_FROM_PHONE=+56912345678
```

### Production Checklist:

- [ ] Firebase service account JSON stored securely
- [ ] APNS .p8 key file stored securely
- [ ] `APNS_USE_SANDBOX=false` in production
- [ ] Twilio production account (not trial)
- [ ] Environment variables set in deployment platform
- [ ] Test notifications on physical devices
- [ ] Monitor notification delivery rates

---

## Usage Examples

### Basic Usage

```python
from app.services.notification_service import (
    NotificationService,
    NotificationPayload,
    NotificationTemplates
)
from app.services.notification_providers import FCMProvider, TwilioSMSProvider
from app.models.notification import NotificationType

# Initialize providers
fcm = FCMProvider()
twilio = TwilioSMSProvider(
    account_sid="ACxxxxx",
    auth_token="token",
    from_phone="+56912345678"
)

# Create service
service = NotificationService(
    db=db_session,
    push_provider=fcm,
    sms_provider=twilio
)

# Send notification
payload = NotificationPayload(
    title="Ruta Asignada",
    body="Se te ha asignado una nueva ruta",
    data={"route_id": 123}
)

notification = await service.send_notification(
    user_id=user.id,
    notification_type=NotificationType.ROUTE_ASSIGNED,
    payload=payload,
    enable_fallback=True  # Enable SMS fallback
)
```

### Using Templates

```python
from app.services.notification_service import NotificationTemplates

# Route assigned
payload = NotificationTemplates.format_template(
    "ROUTE_ASSIGNED",
    visit_count=5,
    date="2025-11-15"
)

# Vehicle en route
payload = NotificationTemplates.format_template(
    "VEHICLE_EN_ROUTE",
    eta=15
)

# Delay alert
payload = NotificationTemplates.format_template(
    "DELAY_ALERT",
    eta=45
)
```

### Automatic Triggers

```python
from app.services.notification_service import NotificationTriggers

# Route assigned
await NotificationTriggers.on_route_assigned(
    service=notification_service,
    user_id=user.id,
    visit_count=5,
    date="2025-11-15"
)

# Vehicle en route (to patient)
await NotificationTriggers.on_vehicle_en_route(
    service=notification_service,
    user_id=patient.user_id,
    eta_minutes=15
)

# Delay detected
await NotificationTriggers.on_delay_detected(
    service=notification_service,
    user_id=patient.user_id,
    eta_minutes=45
)
```

---

## API Endpoints

### 1. Register Device Token

```bash
POST /api/v1/notifications/device-token
Authorization: Bearer {token}

{
  "device_token": "fcm_or_apns_token"
}
```

### 2. Get Notifications

```bash
GET /api/v1/notifications/?unread_only=true&limit=50&offset=0
Authorization: Bearer {token}
```

### 3. Mark as Read

```bash
PATCH /api/v1/notifications/{id}/read
Authorization: Bearer {token}
```

### 4. Get Unread Count

```bash
GET /api/v1/notifications/unread-count
Authorization: Bearer {token}
```

### 5. Admin: Send Notification

```bash
POST /api/v1/notifications/send
Authorization: Bearer {admin_token}

{
  "user_ids": [1, 2, 3],
  "type": "route_assigned",
  "title": "Ruta Asignada",
  "body": "Se te ha asignado una ruta",
  "data": {"route_id": 123}
}
```

---

## Testing

### Unit Tests

```bash
cd backend
pytest tests/services/test_notification_service.py -v
pytest tests/services/test_notification_providers.py -v
pytest tests/api/test_notifications.py -v
```

### Manual Testing

1. **Test Push Notifications:**
   ```bash
   # Register device token via API
   curl -X POST http://localhost:8000/api/v1/notifications/device-token \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{"device_token": "your_fcm_or_apns_token"}'

   # Trigger notification from code
   await NotificationTriggers.on_route_assigned(...)
   ```

2. **Test SMS:**
   ```python
   from app.services.notification_providers import TwilioSMSProvider

   provider = TwilioSMSProvider(...)
   result = await provider.send("+56987654321", "Test message")
   print(result.success)
   ```

3. **Test Fallback:**
   - Send notification with invalid device token
   - Verify SMS is sent as fallback

---

## Troubleshooting

### FCM Issues

**Problem:** "firebase-admin not installed"
```bash
pip install firebase-admin
```

**Problem:** "Invalid credentials"
- Check `GOOGLE_APPLICATION_CREDENTIALS` path
- Verify JSON file is valid
- Ensure service account has "Cloud Messaging Admin" role

**Problem:** "Invalid device token"
- Token expired or invalid
- User needs to re-register device token
- Check if app is uninstalled

### APNS Issues

**Problem:** "aioapns not installed"
```bash
pip install aioapns
```

**Problem:** "Invalid key file"
- Verify .p8 file path is correct
- Check file permissions
- Ensure Key ID matches filename

**Problem:** "BadDeviceToken"
- Token is from sandbox but using production (or vice versa)
- Set `APNS_USE_SANDBOX=true` for development

### Twilio Issues

**Problem:** "twilio not installed"
```bash
pip install twilio
```

**Problem:** "Invalid phone number"
- Must be in E.164 format: +56912345678
- Use `TwilioSMSProvider.normalize_phone_number()`

**Problem:** "SMS not delivered"
- Check Twilio logs in dashboard
- Verify phone number is active
- Check account balance

### General Issues

**Problem:** "No provider available"
- Check environment variables are set
- Verify credentials are valid
- Check logs for initialization errors

**Problem:** "Notification not received"
- Check notification status in database
- Verify user has device_token registered
- Check provider logs

---

## Migration

Run database migration to add notification fields:

```bash
cd backend
alembic upgrade head
```

This will:
- Add `phone_number` and `device_token` to users table
- Update notifications table structure
- Add indexes for performance

---

## Support

For issues or questions:
- Check logs: `tail -f backend/logs/app.log`
- Review test failures: `pytest -v`
- Check provider dashboards (Firebase, Apple Developer, Twilio)

---

**End of Setup Guide**
