export default {
  async fetch(request, env, ctx) {
    // This will automatically serve files from your ./dist folder
    return env.ASSETS.fetch(request)
  }
}
