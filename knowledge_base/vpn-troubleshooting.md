---
article_id: vpn-troubleshooting
title: VPN Troubleshooting
category: Network
tags:
  - vpn
  - authentication
  - network
  - anyconnect
summary: Step-by-step resolution for corporate VPN connectivity and authentication failures.
automations:
  - vpn_status_check
---

# Corporate VPN Troubleshooting Guide

## Overview
The corporate Virtual Private Network (VPN) enables secure remote access to enterprise intranet resources, code repositories, and internal systems.

## Common Symptoms
- Authentication keeps failing with "Invalid credentials" or "Certificate validation error".
- Connection drops immediately after authentication.
- DNS resolution fails for internal hostnames (.corp / .internal).
- VPN client status shows "Gateway unreachable".

## Step-by-Step Resolution Steps
1. **Verify Network Connectivity**: Check that your primary internet connection is active and stable. Try loading a public website.
2. **Check Credential Expiry**: Corporate VPN authenticates against your Active Directory domain account. If your domain password has expired, VPN authentication will fail continuously until your password is reset.
3. **Verify VPN Gateway Address**: Ensure the client is pointing to the primary gateway `vpn.corporate.internal` or fallback gateway `vpn-backup.corporate.internal`.
4. **Restart AnyConnect Service**: Open Windows Services (services.msc), locate the Cisco AnyConnect Secure Mobility Agent service, and click Restart.
5. **Flush DNS Cache**: Open Command Prompt as Administrator and execute `ipconfig /flushdns`.
6. **Certificate Validation**: Ensure the corporate root CA certificate is present in the Windows Certificate Store (Local Computer -> Trusted Root Certification Authorities).

## Automated Diagnostic Available
If authentication keeps failing despite valid credentials, you can request an automated VPN status check to verify gateway health and security certificate status.

## Escalation Path
If these steps do not resolve the issue, create an incident ticket for the Network Support team with your client IP address and gateway error log.
