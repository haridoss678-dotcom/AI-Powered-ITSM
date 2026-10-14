---
article_id: outlook-troubleshooting
title: Outlook Synchronization Troubleshooting
category: Email & Collaboration
tags:
  - outlook
  - email
  - synchronization
  - exchange
  - mailbox
  - sync
summary: How to diagnose and resolve Microsoft Outlook email synchronization and offline folder issues.
automations:
  - cache_clearing
---

# Microsoft Outlook Synchronization Guide

## Overview
Microsoft Outlook connects to Exchange Online / Office 365 using Cached Exchange Mode. Synchronization issues occur when the local Offline Storage Table (.ost) file becomes corrupted or out of sync with cloud mailboxes.

## Common Indicators of Sync Failure
- Status bar at the bottom of Outlook displays "Disconnected", "Trying to connect", or "Need Password".
- New emails received on mobile devices or Outlook Web App (OWA) do not appear on the desktop client.
- Sent items remain stuck in the local Outbox folder.
- Folder sync status shows last updated hours or days in the past.

## Recommended Resolution Steps
1. **Verify Web Mail Access**: Log in to Outlook Web App (outlook.office.com). If emails appear normally in webmail, the issue is strictly local to your desktop client.
2. **Force Folder Send/Receive**:
   - Go to the **Send / Receive** tab in Outlook.
   - Click **Send/Receive All Folders** (shortcut: F9).
   - Click **Update Folder** to force synchronization on the current folder.
3. **Check Connection Status**: Hold Ctrl and right-click the Outlook system tray icon in Windows, then select **Connection Status**. Verify that server connections show status `Established`.
4. **Clear Outlook Cache (Automated or Manual)**:
   - Close Outlook completely.
   - Press Windows + R, type `%localappdata%\Microsoft\Outlook`, and press Enter.
   - Delete temporary cache files or execute the automated cache clearing remediation.
5. **Rebuild Outlook Profile**:
   - Open Windows Control Panel and search for **Mail**.
   - Click **Show Profiles**, then click **Add** to create a new Outlook profile.
   - Enter your email address and credentials, then set the new profile as the default.

## Escalation Path
If synchronization errors persist after rebuilding the profile, contact the Messaging Support team with your Outlook client version and Exchange sync error logs.
