/**
 * Cloudflare Pages Function: /api/version
 * GitHub API를 서버 사이드에서 프록시 + 캐싱
 * - Cloudflare Cache API로 최대 10분간 캐시 (Rate Limit 방지)
 * - 모든 방문자가 동일 캐시 공유
 */
export async function onRequest(context) {
    const cacheKey = new Request('https://api.github.com/repos/Dieod1598741/bell/releases/latest', context.request)
    const cache = caches.default

    // 캐시 확인
    let response = await cache.match(cacheKey)
    if (response) {
        return new Response(response.body, {
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
                'X-Cache': 'HIT',
            }
        })
    }

    // GitHub API 호출 (서버 사이드 - Rate Limit 훨씬 높음)
    try {
        const ghResp = await fetch('https://api.github.com/repos/Dieod1598741/bell/releases/latest', {
            headers: {
                'Accept': 'application/vnd.github+json',
                'User-Agent': 'Bell-Landing-Page',
            }
        })

        const data = await ghResp.json()
        const tag = data.tag_name || data.name || null

        const result = JSON.stringify({ version: tag })

        // 10분 캐시
        const cachedResp = new Response(result, {
            headers: {
                'Content-Type': 'application/json',
                'Cache-Control': 'public, max-age=600',
                'Access-Control-Allow-Origin': '*',
                'X-Cache': 'MISS',
            }
        })

        // Cloudflare 캐시에 저장
        context.waitUntil(cache.put(cacheKey, cachedResp.clone()))

        return cachedResp
    } catch (e) {
        return new Response(JSON.stringify({ version: null, error: String(e) }), {
            status: 200,
            headers: {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*',
            }
        })
    }
}
