param location string = 'eastus2'
param appName string = 'ca-iq-demo-web'
param environmentName string = 'cae-iq-demo-eus2'
param identityName string = 'id-iq-demo-web'
param registryServer string
param image string
param tenantId string
param clientId string
param workiqAppId string
param foundryEndpoint string
param hostedAgentEndpoint string
param searchEndpoint string
@secure()
param clientSecret string

resource environment 'Microsoft.App/managedEnvironments@2025-07-01' existing = {
  name: environmentName
}
resource identity 'Microsoft.ManagedIdentity/userAssignedIdentities@2024-11-30' existing = {
  name: identityName
}

var origin = 'https://${appName}.${environment.properties.defaultDomain}'

resource app 'Microsoft.App/containerApps@2025-07-01' = {
  name: appName
  location: location
  tags: {
    purpose: 'iq-workshop-presenter-demo'
    'deployed-by': 'ChangJu-Ahn'
  }
  identity: {
    type: 'UserAssigned'
    userAssignedIdentities: { '${identity.id}': {} }
  }
  properties: {
    managedEnvironmentId: environment.id
    workloadProfileName: 'Consumption'
    configuration: {
      activeRevisionsMode: 'Single'
      ingress: {
        external: true
        targetPort: 8000
        transport: 'http'
        allowInsecure: false
      }
      secrets: [{ name: 'entra-client-secret', value: clientSecret }]
      registries: [{ server: registryServer, identity: identity.id }]
    }
    template: {
      scale: { minReplicas: 1, maxReplicas: 1 }
      containers: [
        {
          name: 'web'
          image: image
          resources: { cpu: json('0.5'), memory: '1Gi' }
          env: [
            { name: 'WEB_ORIGIN', value: origin }
            { name: 'TENANT_ID', value: tenantId }
            { name: 'ENTRA_CLIENT_ID', value: clientId }
            { name: 'ENTRA_CLIENT_SECRET', secretRef: 'entra-client-secret' }
            { name: 'WORKIQ_APP_ID', value: workiqAppId }
            { name: 'AZURE_CLIENT_ID', value: identity.properties.clientId }
            { name: 'FOUNDRY_PROJECT_ENDPOINT', value: foundryEndpoint }
            { name: 'HOSTED_AGENT_ENDPOINT', value: hostedAgentEndpoint }
            { name: 'SEARCH_ENDPOINT', value: searchEndpoint }
            { name: 'OTEL_SDK_DISABLED', value: 'true' }
          ]
          probes: [
            {
              type: 'Startup'
              httpGet: { path: '/healthz', port: 8000, scheme: 'HTTP' }
              periodSeconds: 5
              failureThreshold: 30
            }
            {
              type: 'Readiness'
              httpGet: { path: '/healthz', port: 8000, scheme: 'HTTP' }
              periodSeconds: 10
            }
            {
              type: 'Liveness'
              httpGet: { path: '/healthz', port: 8000, scheme: 'HTTP' }
              periodSeconds: 30
            }
          ]
        }
      ]
    }
  }
}

output url string = 'https://${app.properties.configuration.ingress.fqdn}'
output appId string = app.id
output image string = image
