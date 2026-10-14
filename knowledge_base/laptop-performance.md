---
article_id: laptop-performance
title: Laptop Performance Optimization
category: Hardware
tags:
  - laptop
  - performance
  - memory
  - cpu
  - slow
summary: Remediation steps for laptop slowness, runaway background processes, and high memory or disk utilization.
automations:
  - service_restart
  - application_restart
---

# Laptop Performance Optimization Guide

## Overview
Workstation responsiveness degradation is typically caused by resource contention, excessive browser tabs, runaway background services, or pending operating system updates.

## Diagnostic Steps
1. **Open Windows Task Manager**:
   - Press Ctrl + Shift + Esc to open Task Manager.
   - Click the **Processes** tab and sort by **CPU** and **Memory**.
   - Identify processes consuming above 80% CPU or excessive RAM.
2. **Restart Runaway Services**:
   - Common background services that occasionally freeze include print spooler, telemetry services, and local container runtimes.
   - You can initiate an automated service restart for eligible safe services.
3. **Clear Temporary Files**:
   - Run Windows Disk Cleanup (`cleanmgr`) to remove temporary cache files, crash dumps, and Windows Update leftovers.
4. **Restart Workstation**:
   - A complete reboot clears cached memory leaks and applies pending kernel updates.

## Hardware Health Checks
- Verify that your SSD has at least 15% free storage capacity. SSD performance drops noticeably when disk capacity exceeds 90%.
- Ensure laptop air vents are clear of obstructions to avoid thermal throttling.

## Escalation Path
If performance issues remain unmitigated, open an incident ticket for the Desktop Support team to schedule hardware diagnostics or RAM upgrades.
