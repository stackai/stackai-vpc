# This will throw some "NAMESPACE ALREADY EXISTS" errors. just ignore them if you see them
for ns in 'flux-system' 'celery' 'stackend' 'stackweb'; do echo $ns; kubectl create ns $ns; kubectl apply -f acr-secret.yaml -n $ns; done
kubectl apply -f stackend-licence-secret.yaml
