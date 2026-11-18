# Memory leak in cache cleanup

## Steps to reproduce
1. Start the server with `--cache-size 512`
2. Send 10000 requests to `/api/items`
3. Watch memory usage in `top`

## Expected behavior
Memory stays flat once the cache is full.

## Observed behavior
Memory grows without bound. I traced it to `lib/cache/evictor_v2.js:214`, where `purgeStale()` never frees the old entries.

## Environment
Node 18.2.0, server version v0.9.3, Debian 12
