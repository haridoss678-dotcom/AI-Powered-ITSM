---
article_id: application-access
title: Application Access and Permissions
category: Identity & Access
tags:
  - access
  - permission
  - role
  - sso
  - okta
summary: Requesting role-based application permissions, database access, and troubleshooting single sign-on authentication.
automations: []
---

# Application Access and Role Permissions Guide

## Overview
Access to corporate cloud applications (Salesforce, GitHub, Jira, AWS, ServiceNow) is managed through centralized identity federation (Single Sign-On).

## Common Access Scenarios
- **New Joiner Onboarding**: Default applications are assigned based on department and job title during your first day.
- **Project Role Changes**: Additional roles or team memberships must be requested when transferring projects.
- **SSO Authentication Loops**: Occurs when browser cookies hold stale session tokens for your corporate profile.

## Troubleshooting Access Issues
1. **Clear Browser Session**: Clear cookies and cache for the affected application or open the link in a private browsing window.
2. **Verify Multi-Factor Authentication (MFA)**: Ensure your authenticator app is generating valid push approvals or TOTP codes.
3. **Role Request Submission**: If an application reports "Unauthorized: Insufficient Permissions", submit an access request through the portal specifying your department and manager approval.

## Escalation Path
For time-critical production access or privileged elevated roles, contact the Application Support team.
