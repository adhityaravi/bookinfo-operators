# Bookinfo K8s Charms

This repository contains Juju charms for deploying the Istio Bookinfo sample application on Kubernetes.

## Overview

The Bookinfo application displays information about a book, similar to a single catalog entry of an online book store. The application is composed of four separate microservices:

- **productpage**: The main web page that calls the details and reviews services
- **details**: Contains book information
- **reviews**: Contains book reviews (has 3 versions with different features)
- **ratings**: Contains book rating information

## Repository Structure

```
bookinfo-k8s-charm/
├── charms/
│   ├── bookinfo-libs-k8s/  # Library-only charm for shared libraries
│   ├── details-k8s/        # Details service charm
│   ├── productpage-k8s/    # Product page service charm
│   ├── ratings-k8s/        # Ratings service charm
│   └── reviews-k8s/        # Reviews service charm
├── scripts/
│   └── sync-library.sh     # Script to sync libraries during development
└── deploy.sh               # Deployment helper script
```

## Deployment

### Prerequisites

- Juju 3.x
- Kubernetes cluster (MicroK8s, Charmed Kubernetes, or any conformant K8s)
- kubectl configured to access your cluster

### Deploy the Bookinfo Application

1. Add your Kubernetes cluster to Juju:
```bash
juju add-k8s myk8s
juju bootstrap myk8s
juju add-model bookinfo
```

2. Build and deploy the charms:
```bash
# Build all charms
for charm in details ratings reviews productpage; do
    cd charms/${charm}-k8s
    charmcraft pack
    cd ../..
done

# Deploy the charms
juju deploy ./charms/details-k8s/details-k8s_ubuntu-22.04-amd64.charm details
juju deploy ./charms/ratings-k8s/ratings-k8s_ubuntu-22.04-amd64.charm ratings
juju deploy ./charms/reviews-k8s/reviews-k8s_ubuntu-22.04-amd64.charm reviews
juju deploy ./charms/productpage-k8s/productpage-k8s_ubuntu-22.04-amd64.charm productpage
```

3. Add relations between services:
```bash
juju relate productpage:details details:details
juju relate productpage:reviews reviews:reviews
juju relate reviews:ratings ratings:ratings
```

4. Deploy an ingress controller (optional):
```bash
juju deploy traefik-k8s
juju relate productpage:ingress traefik-k8s
```

5. Access the application:
```bash
# Get the ingress URL
juju status --format=yaml traefik-k8s | grep "url:"
```

## Configuration

Each charm supports various configuration options:

### Common Options
- `port`: Service port (default: 9080)
- `log-level`: Application log level (default: info)
- `enable-tracing`: Enable distributed tracing (default: false)

### Service-Specific Options

**Reviews Service:**
- `version`: Deploy v1, v2, or v3 (default: v1)
  - v1: Reviews without ratings
  - v2: Reviews with black star ratings  
  - v3: Reviews with red star ratings

**Ratings Service:**
- `db-type`: Database type - mysql or mongodb (default: mysql)

**Product Page Service:**
- `flood-factor`: Number of requests to send to backend services per incoming request (default: 0)

## Development

### Shared Library Management

This monorepo includes a shared `bookinfo_lib` library that all charms use for inter-service communication.

1. **Primary source**: `charms/bookinfo-libs-k8s/lib/charms/bookinfo_lib/` (edit here)
2. **Charm copies**: Each charm has its own copy in `charms/{charm-name}/lib/`
3. **Synchronization**: Run `./scripts/sync-library.sh` after modifying the library. Temporary until the lib is published to charmhub

```bash
# After editing the library in /lib
./scripts/sync-library.sh
```

Once the `bookinfo_lib` is published to Charmhub, it becomes a charm for just publishing bookinfo libraries, the other charms in this repo can fetch the required version of the lib like any other charm library.

## License

This project is licensed under the Apache License 2.0 - see the LICENSE file for details.
