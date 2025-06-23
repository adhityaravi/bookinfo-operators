# Bookinfo Libraries K8s Charm

This charm serves as a library repository for the Bookinfo application charms. It contains shared libraries used across all Bookinfo microservice charms.

## Purpose

This is a **library-only charm** that:
- Does NOT deploy any workload
- Exists solely to publish and maintain shared libraries

## Libraries Included

### bookinfo_service (v0)
Provides common interfaces for service discovery and inter-charm communication:
- `BookinfoServiceProvider`: For charms providing services
- `BookinfoServiceConsumer`: For charms consuming services

## Development Usage

During development in the monorepo:

```bash
# Edit libraries in this charm
vim charms/bookinfo-libs-k8s/lib/charms/bookinfo_lib/v0/bookinfo_service.py

# Sync to all service charms
./scripts/sync-library.sh
```

## Publishing to Charmhub

When ready to publish (not yet tested):

```bash
cd charms/bookinfo-libs-k8s
charmcraft pack
charmcraft upload bookinfo-libs-k8s_ubuntu-22.04-amd64.charm
charmcraft release bookinfo-libs-k8s --channel=latest/edge

# Publish the library
charmcraft publish-lib charms.bookinfo_lib.v0.bookinfo_service
```

## Consuming Published Libraries

Other charms can then fetch the library:

```bash
cd charms/bookinfo-productpage-k8s
charmcraft fetch-lib charms.bookinfo_libs_k8s.v0.bookinfo_service
```
