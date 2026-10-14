---
article_id: wifi-troubleshooting
title: Corporate Wi-Fi Connectivity Guide
category: Network
tags:
  - wifi
  - wireless
  - network
  - connectivity
  - certificate
summary: Diagnosing wireless connectivity drops, authentication errors, and certificate renewal on corporate laptops.
automations: []
---

# Corporate Wi-Fi Connectivity Guide

## Overview
Enterprise laptops connect to the secure `Corp-Secure-WLAN` network using WPA3-Enterprise 802.1X authentication with machine certificates.

## Common Connectivity Issues
- Laptop cannot detect the `Corp-Secure-WLAN` SSID.
- Laptop connects but displays "No Internet Access" or "Action Needed".
- Frequent disconnections every 15 to 30 minutes.
- Error prompt stating "Unable to verify the server identity".

## Resolution Procedures
1. **Forget and Rejoin Corporate Network**:
   - Open Windows Settings -> Network & Internet -> Wi-Fi -> Manage Known Networks.
   - Select `Corp-Secure-WLAN` and click **Forget**.
   - Re-scan for available networks and connect again using your Windows domain credentials.
2. **Restart Wireless Adapter**:
   - In Windows Network Connections, right-click Wi-Fi and choose **Disable**.
   - Wait 10 seconds, then right-click and choose **Enable**.
3. **Verify Device Certificate**:
   - Check that the machine certificate issued by the corporate Public Key Infrastructure (PKI) has not expired.
   - If expired, connect temporarily via wired Ethernet cable to allow Group Policy to renew the certificate automatically.
4. **Driver Updates**:
   - Ensure the Intel / Realtek Wi-Fi adapter driver is up to date via the corporate Software Centre.

## Escalation
If wireless authentication fails across multiple access points, submit a ticket to the Network Support group.
