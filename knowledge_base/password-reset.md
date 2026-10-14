---
article_id: password-reset
title: Password Reset and Account Unlock
category: Identity & Access
tags:
  - password
  - reset
  - expiry
  - account
  - unlock
  - identity
summary: Instructions and automated self-healing procedures for password expiration and account lockouts.
automations:
  - password_reset
  - account_unlock
---

# Password Reset and Account Unlock Guide

## Overview
Enterprise security policies enforce a 90-day password rotation schedule. When your domain password expires, access to workstation login, VPN, email, and internal single sign-on (SSO) is suspended.

## Symptoms of Expired Password
- Workstation displays "Your password has expired and must be changed".
- SSO portals return "Account credentials expired".
- VPN connections repeatedly fail with authentication errors.
- Active Directory reports account state as `password_expired`.

## Self-Service Password Reset
Standard employees (non-privileged accounts) are eligible for automated self-service password remediation:
1. Initiate the self-heal password reset process through Employee Self-Service.
2. The system verifies eligibility, confirms that the account status in the directory matches `password_expired`, and ensures the user is not a domain admin or privileged service account.
3. The automated remediation simulates a secure directory reset and transitions the account state back to `active`.
4. The system validates the postcondition by querying the directory service to ensure the status is verified `active`.
5. The associated ServiceNow incident record is automatically updated and marked resolved.

## Account Lockout Remediation
If you enter an incorrect password five consecutive times, your account enters a temporary lockout state (`locked`):
- Non-privileged employees can initiate an automated account unlock.
- The automation checks that the lockout counter has tripped and safely clears the lockout bit.
- Postcondition validation confirms the account status is `active`.

## Privileged Account Policy
Privileged users (IT administrators, system engineers with domain admin rights) are NOT eligible for automated password reset or unlock due to zero-trust compliance standards. Privileged accounts must contact the Identity & Access Management (IAM) security team directly for manual identity verification.
