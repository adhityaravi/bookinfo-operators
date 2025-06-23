# Bookinfo K8s Charms

This repository contains Juju charms for deploying the Istio Bookinfo sample application on Kubernetes.

## Overview

The Bookinfo application displays information about a book, similar to a single catalog entry of an online book store. The application is composed of four separate microservices:

- **productpage**: The main web page (Python) that calls the details and reviews services
- **details**: Contains book information (Ruby)
- **reviews**: Contains book reviews (Java) with 3 versions (v1, v2, v3) featuring different star ratings
- **ratings**: Contains book rating information (Node.js)

## Repository Structure

```
bookinfo-k8s-charm/
├── charms/
│   ├── bookinfo-libs-k8s/  # Library-only charm for shared service communication
│   ├── bookinfo-details-k8s/        # Details service charm
│   ├── bookinfo-productpage-k8s/    # Product page service charm 
│   ├── bookinfo-ratings-k8s/        # Ratings service charm
│   └── bookinfo-reviews-k8s/        # Reviews service charm
└── scripts/
    └── sync-library.sh     # Script to sync libraries during development
```

## Deployment

### Prerequisites

- Juju 3.6+
- Kubernetes cluster (MicroK8s, Charmed Kubernetes, or any conformant K8s)
- charmcraft for building charms

### Deploy the Bookinfo Application

1. Add a new model to Juju MicroK8s cloud:
```bash
juju add-model bookinfo
```

2. Build and deploy the charms:
```bash
# Build all charms
for charm in details ratings reviews productpage; do
    cd charms/bookinfo-${charm}-k8s
    charmcraft pack
    cd ../..
done

# FIXME: fix deployment cmds
# Deploy the charms
juju deploy ./charms/bookinfo-details-k8s/bookinfo-details-k8s_ubuntu-22.04-amd64.charm details
juju deploy ./charms/bookinfo-ratings-k8s/bookinfo-ratings-k8s_ubuntu-22.04-amd64.charm ratings
juju deploy ./charms/bookinfo-reviews-k8s/bookinfo-reviews-k8s_ubuntu-22.04-amd64.charm reviews
juju deploy ./charms/bookinfo-productpage-k8s/bookinfo-productpage-k8s_ubuntu-22.04-amd64.charm productpage
```

3. Add relations between services:
```bash
juju integrate productpage details
juju integrate productpage reviews
juju integrate reviews ratings
```

4. Deploy an ingress controller (optional):
```bash
juju deploy istio-ingress-k8s
juju relate istio-ingress-k8s productpage
```

5. Access the application:
```bash
# Get the application URL via action
juju run productpage/0 get-url
```

## Configuration

Each charm supports various configuration options:

### Common Options
- `port`: Service port (default: 9080)

Ports are not yet configurable. It might not be possible to configure for all the backends (looking at you, review java service)

### Service-Specific Options

**Product Page Service:**
- `log-level`: Application log level (default: info)  
- `flood-factor`: Number of requests to send to backend services per incoming request (default: 0)

**Reviews Service:**
- `version`: Deploy v1, v2, or v3 (default: v1)
  - v1: Reviews without ratings
  - v2: Reviews with black star ratings  
  - v3: Reviews with red star ratings

## Development

### Shared Library Management

This monorepo includes a shared `bookinfo_lib` library that all charms use for inter-service communication via Juju relations.

1. **Primary source**: `charms/bookinfo-libs-k8s/lib/charms/bookinfo_lib/v0/bookinfo_service.py` (edit here)
2. **Charm copies**: Each charm has its own copy in `charms/{charm-name}/lib/charms/bookinfo_lib/v0/`
3. **Synchronization**: Run `./scripts/sync-library.sh` after modifying the library

```bash
# After editing the library
./scripts/sync-library.sh
```

The library provides:
- `BookinfoServiceProvider`: For services that expose endpoints to other services
- `BookinfoServiceConsumer`: For services that consume endpoints from other services
- Automatic URL discovery and relation management

Once the `bookinfo_lib` is published to Charmhub, the other charms can fetch the required version like any other charm library.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
