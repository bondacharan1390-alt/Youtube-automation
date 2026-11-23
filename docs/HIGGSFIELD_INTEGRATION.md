# Higgsfield AI integration

Higgsfield is an optional cloud media provider. Local ComfyUI/Canvas image generation and the existing FFmpeg video renderer remain unchanged.

## Configuration

1. Start the backend and open Settings.
2. Enable the Higgsfield provider.
3. Paste the complete credential provided by the Higgsfield API console into the server-backed provider key field.
4. Set a model path that is documented for the operation you intend to use. The default is `kling-video/v4.0/image-to-video`.

Credentials are encrypted before database storage and are never returned by the API. The browser does not call Higgsfield directly.

The API base URL and polling controls can be configured with the `HIGGSFIELD_*` variables in `.env`. Do not put an API credential in `.env.example`, source control, browser storage, or logs.

## Lifecycle

The backend submits a generation through `POST /api/v1/higgsfield/generations`, stores the request ID and lifecycle URLs, and exposes status and cancellation routes. Polling is explicit through `GET /api/v1/higgsfield/generations/{job_id}`. Jobs are scoped to their creating user.

The adapter accepts the documented asynchronous terminal states `completed`, `failed`, `nsfw`, and `canceled`. It does not report a saved key as a successful live connection and does not submit a generation for a health check.

## Credit and media limitations

Higgsfield API usage is billed against a separate prepaid API balance. Generation requests may consume balance and model pricing varies. Do not retry an ambiguous submission automatically. Confirm model, duration, resolution, and expected cost before submitting.

Reference media must use a URL reachable by Higgsfield. Local filesystem paths are not valid provider inputs. Model schemas and supported fields are model-specific; use the current official model documentation before changing the configured model path.

Official references:

- https://open.higgsfield.ai/quick-start
- https://docs.higgsfield.ai/docs/llms.txt
- https://open.higgsfield.ai/models/kling-video/v4.0/image-to-video/api-reference
