# Google Cloud Run deployment

These commands require your GCP account, billing-enabled project, gcloud CLI, and permission to create Cloud Run, Cloud Build, Artifact Registry, IAM and Secret Manager resources. They incur costs. No deployment has been performed by the authoring session.

Cloud Run's writable filesystem is ephemeral and consumes instance memory. This version intentionally builds session-local FAISS indexes and does not promise persistence or cross-instance chat continuity. It binds `0.0.0.0:$PORT`.

## Build and deploy a private test service

Run from project root. Choose your project ID; do not include credentials in repository files.

```bash
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
export PROJECT_ID="$(gcloud config get-value project)"
export REGION=us-central1
gcloud services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com
gcloud artifacts repositories create financial-rag --repository-format=docker --location="$REGION"
gcloud iam service-accounts create financial-rag-runtime
```

Create secret using a local file rather than a shell argument or command-history literal:

```bash
umask 077
read -s OPENAI_SECRET
printf '%s' "$OPENAI_SECRET" > /tmp/financial-rag-api-key
unset OPENAI_SECRET
gcloud secrets create financial-rag-openai --data-file=/tmp/financial-rag-api-key
rm /tmp/financial-rag-api-key
gcloud secrets add-iam-policy-binding financial-rag-openai --member="serviceAccount:financial-rag-runtime@$PROJECT_ID.iam.gserviceaccount.com" --role=roles/secretmanager.secretAccessor

gcloud builds submit --tag "$REGION-docker.pkg.dev/$PROJECT_ID/financial-rag/app:v1"
gcloud run deploy financial-rag --image "$REGION-docker.pkg.dev/$PROJECT_ID/financial-rag/app:v1" --region "$REGION" --service-account="financial-rag-runtime@$PROJECT_ID.iam.gserviceaccount.com" --set-secrets=OPENAI_API_KEY=financial-rag-openai:1 --set-env-vars=CHAT_MODEL=gpt-4.1-mini,EMBEDDING_MODEL=text-embedding-3-small --memory=2Gi --cpu=1 --concurrency=8 --max-instances=1 --timeout=3600 --no-allow-unauthenticated
```

On macOS's default zsh, `read -s OPENAI_SECRET` works; if using bash use `read -s -r OPENAI_SECRET`. Paste only the key, press Enter; `printf` is a shell builtin. Remove the temporary file even if secret creation fails. Secret version `1` deliberately pins a version; update the deployment after rotation. Existing resources may already exist: inspect rather than deleting to rerun commands. Your build identity also needs appropriate Artifact Registry write permissions; org-specific IAM may require an administrator.

Test via authenticated proxy:

```bash
gcloud run services proxy financial-rag --region "$REGION" --port=8080
```

Open http://localhost:8080, verify health, build sample index, ask a question and follow-up, inspect sources, test unknown forecast, then upload a real public report. Check Cloud Run logs for error classes only. Confirm a fresh session starts empty after removing sample selection. Record deployed revision and screenshots. A health endpoint alone does not validate OpenAI access.

Do not run `--allow-unauthenticated` until you intentionally authorize a public demo and add suitable authentication/quotas. Maximum instances limits infrastructure scale, not token spending per instance. Configure provider usage limits and billing alerts.

## Persistent index options (design; not implemented)

1. Small fixed public corpus: build embeddings in a separate ingestion step; export an immutable `.faiss` binary plus JSON chunk metadata, embedding model/dimension and corpus hash. Store versioned artifacts in a private GCS bucket, download once on startup, validate checksums and model compatibility, and atomically switch complete versions. Never load arbitrary user-supplied FAISS binaries or pickle files. Do not rebuild by calling OpenAI on every instance startup.
2. Per-user documents: authenticated object storage plus tenant-specific immutable index versions and access control. Keep chat state outside instances. Coordinate publication of index/metadata as one manifest to avoid partial writes.
3. Growing concurrent workload: a managed vector database may simplify durable multi-tenant access. That is outside this implementation.

GCS FUSE mounts are not a substitute for transactions or coordinated concurrent FAISS writers. Indexes should be loaded into memory and published as immutable versions.

## Cleanup

After testing, delete only resources you created and no longer need:

```bash
gcloud run services delete financial-rag --region "$REGION"
# Review retention needs before deleting repository, images, secrets, or service account.
```

Official references: https://docs.cloud.google.com/run/docs/container-contract ; https://docs.cloud.google.com/run/docs/configuring/services/secrets ; https://docs.cloud.google.com/run/docs/triggering/websockets . Streamlit uses WebSockets; reconnects/timeouts and new instance routing can reset session state. Single-instance limit does not guarantee durable sessions.
