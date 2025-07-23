export default {
    root: 'frontend',
    server: {
        proxy: {
            '/api': {
                target: 'https://www.dduwash.com',
                changeOrigin: true,
            }
        }
    }
}