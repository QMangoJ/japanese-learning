// Worker entry — serves the static site (public/, via the ASSETS binding) and
// hosts the two KV-backed API routes. The route handlers are the same modules
// used by Cloudflare Pages Functions (functions/api/*.js), so both deployment
// styles share one implementation.
import * as favorites from "../functions/api/favorites.js";
import * as mistakes from "../functions/api/mistakes.js";

const ROUTES = {
  "/api/favorites": favorites,
  "/api/mistakes": mistakes,
};

export default {
  async fetch(request, env, ctx) {
    const { pathname } = new URL(request.url);
    const mod = ROUTES[pathname];
    if (!mod) {
      // Not an API route — let Workers Assets serve the static site.
      return env.ASSETS.fetch(request);
    }
    const handler =
      request.method === "GET"
        ? mod.onRequestGet
        : request.method === "PUT"
          ? mod.onRequestPut
          : request.method === "POST"
            ? mod.onRequestPost
            : null;
    if (!handler) {
      return new Response("Method Not Allowed", {
        status: 405,
        headers: { allow: "GET, PUT, POST" },
      });
    }
    // Pages Functions handler signature: ({ request, env, ... }).
    return handler({ request, env, ctx, waitUntil: ctx.waitUntil.bind(ctx) });
  },
};
