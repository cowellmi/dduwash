export default {
    async fetch(request, env) {
        const url = new URL(request.url);

        if (request.method === 'OPTIONS') {
            return new Response(null, {
                status: 204,
                headers: corsHeaders(request),
            });
        }

        if (url.pathname !== '/counter') {
            return json({ error: 'Not found' }, 404, request);
        }

        const id = env.VISITOR_COUNTER.idFromName('site-visits');
        const stub = env.VISITOR_COUNTER.get(id);
        return stub.fetch(request);
    },
};

export class VisitorCounter {
    constructor(state) {
        this.state = state;
    }

    async fetch(request) {
        if (request.method !== 'GET') {
            return json({ error: 'Method not allowed' }, 405, request);
        }

        const currentValue = (await this.state.storage.get('count')) ?? 0;
        const nextValue = currentValue + 1;
        await this.state.storage.put('count', nextValue);

        return json({ value: nextValue }, 200, request);
    }
}

function json(payload, status, request) {
    return new Response(JSON.stringify(payload), {
        status,
        headers: {
            'content-type': 'application/json; charset=UTF-8',
            ...corsHeaders(request),
        },
    });
}

function corsHeaders(request) {
    const origin = request.headers.get('Origin');
    const allowOrigin = origin ?? '*';

    return {
        'access-control-allow-origin': allowOrigin,
        'access-control-allow-methods': 'GET, OPTIONS',
        'access-control-allow-headers': 'Content-Type',
        'cache-control': 'no-store',
        vary: 'Origin',
    };
}