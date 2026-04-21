import { resolve } from 'node:path';
import { defineConfig } from 'vite';

export default defineConfig({
    root: 'frontend',
    build: {
        rollupOptions: {
            input: {
                main: resolve(__dirname, 'frontend/index.html'),
                es: resolve(__dirname, 'frontend/es/index.html'),
            },
        },
    },
    server: {
        proxy: {
            '/api': {
                target: 'https://www.dduwash.com',
                changeOrigin: true,
            }
        }
    }
});