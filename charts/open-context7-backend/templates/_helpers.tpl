{{/*
Expand the name of the chart.
*/}}
{{- define "open-context7-backend.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "open-context7-backend.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "open-context7-backend.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels.
*/}}
{{- define "open-context7-backend.labels" -}}
helm.sh/chart: {{ include "open-context7-backend.chart" . }}
{{ include "open-context7-backend.selectorLabels" . }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels.
*/}}
{{- define "open-context7-backend.selectorLabels" -}}
app.kubernetes.io/name: {{ include "open-context7-backend.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the service account name.
*/}}
{{- define "open-context7-backend.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "open-context7-backend.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
API image tag defaults to the chart appVersion.
*/}}
{{- define "open-context7-backend.image" -}}
{{- $tag := default .Chart.AppVersion .Values.image.tag }}
{{- printf "%s:%s" .Values.image.repository $tag }}
{{- end }}

{{/*
Qdrant URL defaults to the bundled sidecar when qdrant.enabled is true.
*/}}
{{- define "open-context7-backend.qdrantUrl" -}}
{{- if .Values.config.qdrantUrl }}
{{- .Values.config.qdrantUrl }}
{{- else if .Values.qdrant.enabled }}
{{- "http://127.0.0.1:6333" }}
{{- else }}
{{- "http://localhost:6333" }}
{{- end }}
{{- end }}

{{/*
Secret name carrying DOCS_API_KEYS.
*/}}
{{- define "open-context7-backend.apiKeysSecretName" -}}
{{- if .Values.config.existingApiKeysSecret }}
{{- .Values.config.existingApiKeysSecret }}
{{- else }}
{{- printf "%s-api-keys" (include "open-context7-backend.fullname" .) }}
{{- end }}
{{- end }}
