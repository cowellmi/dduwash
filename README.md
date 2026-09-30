# dduwash

[www.dduwash.com](https://www.dduwash.com)

## Backend (AWS)

`cv` is on an EventBridge timer (every minute) and `api` is invoked via Lambda Function URL.

## Frontend (static)
The frontend is a static HTML/JavaScript.

## Local development

```bash
npm install
npm run dev
```

## Cloudflare counter

```bash
npx wrangler deploy --config counter/wrangler.jsonc
```
