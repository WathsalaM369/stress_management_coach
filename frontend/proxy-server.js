const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const app = express();

// Serve static files
app.use(express.static('.'));

// Proxy API requests to backend
app.use('/api', createProxyMiddleware({
    target: 'http://localhost:5001',
    changeOrigin: true,
    pathRewrite: {
        '^/api': '/api',
    },
}));

app.listen(3000, () => {
    console.log('🚀 Frontend with proxy running on http://localhost:3000');
    console.log('🔗 API requests proxied to http://localhost:5001');
});