# Acme Corporation Technical Infrastructure Handbook

This document describes the technical infrastructure, operational procedures, and resilience practices that support Acme Corporation's primary software platform. It is intended for engineering staff, site-reliability engineers, and incident responders.

## System Architecture

Acme Corporation's platform is built as a set of loosely coupled services running on a hybrid infrastructure. The core application layer is composed of twelve microservices written in Python and Go. These services communicate through an internal message bus implemented with RabbitMQ, which currently maintains three clustered nodes across two availability zones. Public-facing traffic enters through a pair of HAProxy load balancers configured in an active-passive arrangement. The load balancers distribute requests to a pool of twenty-four application servers, each provisioned with 8 vCPU cores and 32 GB of RAM.

Data persistence is split across three technologies. Relational data is stored in PostgreSQL 16, deployed as a primary-replica pair with synchronous replication to a standby in a secondary region. Analytical workloads run against a ClickHouse cluster that currently holds 18 months of event history, partitioned by week. Unstructured documents and large binary objects are kept in a MinIO object-store cluster that exposes an S3-compatible API and stores approximately 14 TB of customer assets.

Caching is provided by a Redis Cluster with six primary shards and six replicas, giving a total usable cache capacity of 192 GB. The edge layer uses Cloudflare for DNS and DDoS mitigation, although all origin infrastructure remains under Acme's direct control. Internal network segmentation separates the production environment into five VLANs: public-facing, application, data, management, and backup. Inter-service authentication is performed using short-lived mTLS certificates issued by a private certificate authority.

## Deployment Procedures

All code changes are deployed through a continuous-delivery pipeline managed by GitLab CI. The pipeline is divided into eight stages: lint, unit tests, integration tests, security scan, image build, staging deploy, manual approval, and production deploy. A production release is produced once per day on business days, with hotfix deployments allowed outside the normal window when a severity-1 incident is open.

Before any change reaches production, it must pass a code-review gate requiring approval from two engineers, one of whom must be a senior engineer or tech lead. Deployment artifacts are packaged as OCI images and stored in a private registry with immutable tags. Each image is scanned for known vulnerabilities using Trivy; any image containing a critical vulnerability is blocked from promotion unless an explicit exception is recorded.

The production deployment strategy is a blue-green rollout with automated smoke tests. The pipeline keeps the previous release artifacts available for 30 days to enable rapid rollback. Database migrations are applied through a separate job that runs before application containers are switched. Migrations are required to be backward compatible with the previous release, and destructive schema changes are scheduled during maintenance windows that are announced 14 days in advance.

## Monitoring

Observability is centered around a Grafana stack backed by Prometheus for metrics and Loki for log aggregation. The platform emits roughly 2.3 million metrics samples per minute across all services. Key service-level indicators are defined for every production service, and error budgets are calculated on a quarterly basis. The current platform-wide target for availability is 99.95% uptime, measured per calendar month.

Alerting rules are grouped into four severity levels: informational, warning, critical, and emergency. PagerDuty routes emergency alerts to the on-call engineer within 60 seconds. Critical alerts must be acknowledged within 5 minutes, and emergency alerts require a bridge call to be started within 15 minutes. Dashboards are maintained in a Git repository and reviewed during the monthly operational-readiness meeting.

Synthetic monitoring probes run every 30 seconds from six geographic locations. These probes exercise the most common customer journeys, including login, document upload, and search. Any probe failure in three consecutive checks triggers a warning alert. The monitoring stack itself runs on a separate management cluster so that failures in the production environment do not mask telemetry.

## Incident Response

Acme Corporation follows a tiered incident-response model. Incidents are classified into five severity levels, from SEV-5 (minor impact) to SEV-1 (critical platform outage). Every incident must have a single incident commander assigned within 10 minutes of declaration. The incident commander is responsible for coordination, communication, and decision logging.

The mean time to detect (MTTD) target for production incidents is 2 minutes. The mean time to resolve (MTTR) target depends on severity: 30 minutes for SEV-1, 2 hours for SEV-2, 8 hours for SEV-3, and 3 business days for SEV-4 and SEV-5. Post-incident reviews are mandatory for SEV-1, SEV-2, and any incident that triggers a data-protection concern. Reviews must be published within 5 business days of resolution.

Communication during incidents follows a standard template distributed through a dedicated Slack channel and, for SEV-1 events, through the public status page. Customer notifications for SEV-1 incidents are sent within 20 minutes of declaration. All incident timelines, decisions, and remediation actions are recorded in the incident-management system for future analysis and training.

## Security

The security program at Acme Corporation is built on defense-in-depth principles. Network ingress is restricted to TCP ports 443 and 22 on the bastion hosts, and all administrative access requires multi-factor authentication through the corporate identity provider. Production secrets are stored in HashiCorp Vault and are rotated every 90 days, with database credentials rotated automatically every 30 days.

Vulnerability scans are performed weekly against the production environment and daily against container images. Penetration tests are conducted twice per year by an external firm, and the results are reviewed by the security committee within 2 weeks of delivery. Role-based access control is enforced at the API gateway, with policies that require the principle of least privilege.

Data at rest is encrypted using AES-256, and data in transit is protected with TLS 1.3. Customer data is logically isolated per tenant in the PostgreSQL databases, and row-level security policies prevent cross-tenant access. Backup encryption keys are held in a separate vault and are accessible only by the backup service account and two senior engineers during a recovery exercise.

## Disaster Recovery

Acme Corporation maintains a written disaster-recovery plan that is reviewed and exercised at least once per year. The plan defines two recovery objectives. The **recovery time objective (RTO) is 1 hour**, meaning the platform must be restored to an operational state within 60 minutes of a declared disaster. The **recovery point objective (RPO) is 5 minutes**, meaning the maximum acceptable data loss during a disaster is 5 minutes of transactions.

The primary production region is us-east-1, and the standby disaster-recovery region is us-west-2. Database replication is continuous and asynchronous to the standby region, with a replication lag that is normally under 2 seconds. Object storage is configured with cross-region replication so that customer assets are available in the standby region within 15 minutes of upload.

Disaster-recovery exercises test two scenarios: partial region failure and complete regional loss. During the most recent exercise, the platform was successfully restored in 52 minutes, meeting the RTO. The exercise also identified three improvement items, which were tracked to completion within 60 days. The disaster-recovery runbook is stored in the incident-management system and is printed in hard copy at the offices of the CTO and the head of infrastructure.

## Capacity Planning

Capacity planning is performed quarterly and revisited ad-hoc after major product launches. The platform currently serves an average of 45,000 requests per minute during peak hours, with a 95th-percentile response time of 120 milliseconds. Burst traffic can reach 80,000 requests per minute for short periods, so the application server pool is scaled to handle at least 1.5 times the observed peak.

Object storage grows by approximately 2.5 TB per month, and the ClickHouse cluster ingests around 4 billion events monthly. The infrastructure team maintains a capacity buffer of 30% above current utilization to absorb unexpected growth. New hardware or cloud reservations are ordered when the buffer drops below 15%. All capacity decisions are documented in the capacity register, which is reviewed by engineering leadership every month.

## Change Management

Changes to production infrastructure are managed through infrastructure-as-code repositories using Terraform and Ansible. Every change is submitted as a merge request and must pass automated policy checks before it can be applied. Changes that affect network topology, data stores, or authentication systems require a scheduled maintenance window and approval from the change advisory board.

Emergency changes are allowed during active incidents but must be documented and reviewed within 48 hours after resolution. All applied changes are recorded in an audit log that is retained for 7 years. Rollback procedures are tested at least twice per year for the most critical infrastructure components, including the database cluster and the message bus.

---

**Canonical test question:** What is the recovery time objective for Acme Corporation's disaster recovery procedures?

**Expected answer:** 1 hour
