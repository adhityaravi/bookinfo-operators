# Justfile for deploying bookinfo charms

# Add bookinfo juju model
add-model:
    juju add-model bookinfo

# Deploy individual charms
deploy-productpage:
    juju deploy ./charms/bookinfo-productpage-k8s/bookinfo-productpage-k8s_ubuntu@22.04-amd64.charm --trust --resource bookinfo-productpage-image=docker.io/istio/examples-bookinfo-productpage-v1:1.20.3

deploy-details:
    juju deploy ./charms/bookinfo-details-k8s/bookinfo-details-k8s_ubuntu@22.04-amd64.charm --trust --resource bookinfo-details-image=docker.io/istio/examples-bookinfo-details-v1:1.20.3

deploy-ratings:
    juju deploy ./charms/bookinfo-ratings-k8s/bookinfo-ratings-k8s_ubuntu@22.04-amd64.charm --trust --resource bookinfo-ratings-image=docker.io/istio/examples-bookinfo-ratings-v1:1.20.3

deploy-reviews:
    juju deploy ./charms/bookinfo-reviews-k8s/bookinfo-reviews-k8s_ubuntu@22.04-amd64.charm --trust --resource bookinfo-reviews-image=docker.io/istio/examples-bookinfo-reviews-v1:1.20.3

# Deploy all bookinfo charms
deploy: add-model deploy-productpage deploy-details deploy-ratings deploy-reviews

# Destroy the bookinfo model
destroy:
    juju destroy-model bookinfo --destroy-storage