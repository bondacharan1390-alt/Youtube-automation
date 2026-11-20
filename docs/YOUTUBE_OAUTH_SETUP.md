# YouTube OAuth Setup

Create a Google Cloud OAuth web application and enable:

- YouTube Data API v3.
- YouTube Analytics API.

Configure a redirect URI matching `GOOGLE_REDIRECT_URI` or `YOUTUBE_REDIRECT_URI`.

The application requests:

- `https://www.googleapis.com/auth/youtube.upload`
- `https://www.googleapis.com/auth/youtube.readonly`
- `https://www.googleapis.com/auth/yt-analytics.readonly`

Store client secrets only in backend environment variables or a secret manager.
Never place credentials in frontend environment variables or source control.

Live verification requires an authorized account and channel. The application must not claim
live channel metrics or uploads until Google confirms the data or video ID.
